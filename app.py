from dash import Dash, html, dcc, Input, Output, State, no_update, callback_context
from flask import session
from dashboard.teacher_view import teacher_layout
from dashboard.student_view import student_layout
from utils.db_utils import get_students_by_filters
from utils.model_utils import predict_risk
import plotly.express as px
from auth import authenticate_teacher, authenticate_student, MAJORS, SEMESTER_CODES, get_sample_students_by_semester_major, init_auth_db
from utils.db_utils import get_student_by_id
from dash.exceptions import PreventUpdate
from dashboard.teacher_view import stat_card
import os

app = Dash(__name__, suppress_callback_exceptions=True)
app.server.secret_key = os.environ.get("DASH_SECRET_KEY", "replace-this-in-production")
init_auth_db()

# Add clientside callback for instant role toggle (no server round-trip needed)
app.clientside_callback(
    """
    function(role) {
        if (role === 'teacher') {
            return [{'display': 'block'}, {'display': 'none'}];
        } else {
            return [{'display': 'none'}, {'display': 'block'}];
        }
    }
    """,
    Output("teacher-inputs", "style"),
    Output("student-inputs", "style"),
    Input("role-toggle", "value"),
)

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            body {
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def login_page():
    return html.Div(
        id="login-container",
        children=[
            # Icon/Logo placeholder
            
            html.H2(
                "Academic Risk Prediction",
                style={
                    "textAlign": "center",
                    "marginBottom": "8px",
                    "fontSize": "24px",
                    "fontWeight": "600",
                    "color": "#1f2937",
                }
            ),
            
            html.P(
                "Sign in to access your dashboard",
                style={
                    "textAlign": "center",
                    "color": "#6b7280",
                    "fontSize": "14px",
                    "marginBottom": "30px",
                }
            ),

            dcc.RadioItems(
                id="role-toggle",
                options=[
                    {"label": " Teacher", "value": "teacher"},
                    {"label": " Student", "value": "student"},
                ],
                value="teacher",
                inline=True,
                style={
                    "textAlign": "center",
                    "marginBottom": "25px",
                    "display": "flex",
                    "justifyContent": "center",
                    "gap": "20px",
                },
                labelStyle={
                    "padding": "8px 16px",
                    "cursor": "pointer",
                }
            ),

            # Teacher login inputs
            html.Div(
                id="teacher-inputs",
                children=[
                    dcc.Input(
                        id="username",
                        placeholder="Teacher Username (e.g., artteacher)",
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "12px 16px",
                            "marginBottom": "12px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "8px",
                            "fontSize": "14px",
                            "boxSizing": "border-box",
                            "transition": "border-color 0.2s",
                        },
                    ),

                    dcc.Input(
                        id="password",
                        type="password",
                        placeholder="Password: (default: 123)",
                        style={
                            "width": "100%",
                            "padding": "12px 16px",
                            "marginBottom": "20px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "8px",
                            "fontSize": "14px",
                            "boxSizing": "border-box",
                            "transition": "border-color 0.2s",
                        },
                    ),
                ],
                style={"display": "block"}
            ),

            # Student login inputs
            html.Div(
                id="student-inputs",
                children=[
                    html.Label(
                        "Select Semester",
                        style={
                            "fontSize": "13px",
                            "fontWeight": "600",
                            "color": "#374151",
                            "marginBottom": "6px",
                            "display": "block",
                        }
                    ),
                    dcc.Dropdown(
                        id="semester-select",
                        options=[{"label": sem, "value": code} for sem, code in SEMESTER_CODES.items()],
                        placeholder="Choose semester...",
                        style={
                            "marginBottom": "12px",
                        }
                    ),
                    
                    html.Label(
                        "Select Major",
                        style={
                            "fontSize": "13px",
                            "fontWeight": "600",
                            "color": "#374151",
                            "marginBottom": "6px",
                            "display": "block",
                        }
                    ),
                    dcc.Dropdown(
                        id="major-select",
                        options=[{"label": f"{major} ({code})", "value": code} for major, code in sorted(MAJORS.items())],
                        placeholder="Choose major...",
                        style={
                            "marginBottom": "12px",
                        }
                    ),
                    
                    html.Label(
                        "Student ID or Select from List",
                        style={
                            "fontSize": "13px",
                            "fontWeight": "600",
                            "color": "#374151",
                            "marginBottom": "6px",
                            "display": "block",
                        }
                    ),
                    dcc.Dropdown(
                        id="student-id-select",
                        options=[],
                        placeholder="Select a student ID or type manually below...",
                        style={
                            "marginBottom": "8px",
                        },
                        searchable=True,
                        clearable=True,
                    ),
                    
                    dcc.Input(
                        id="student-id-manual",
                        placeholder="Enter last digits only (e.g., 10013)",                        
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "12px 16px",
                            "marginBottom": "12px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "8px",
                            "fontSize": "14px",
                            "boxSizing": "border-box",
                        },
                    ),
                    
                    dcc.Input(
                        id="student-password",
                        type="password",
                        placeholder="Password (default: 123)",
                        style={
                            "width": "100%",
                            "padding": "12px 16px",
                            "marginBottom": "20px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "8px",
                            "fontSize": "14px",
                            "boxSizing": "border-box",
                        },
                    ),
                ],
                style={"display": "none"}
            ),

            html.Button(
                "Sign In",
                id="login-btn",
                style={
                    "width": "100%",
                    "padding": "12px",
                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "8px",
                    "fontSize": "15px",
                    "fontWeight": "600",
                    "cursor": "pointer",
                    "transition": "transform 0.2s, box-shadow 0.2s",
                },
            ),

            # Empty div that will be populated by callback
            html.Div(
                id="login-message",
                style={
                    "marginTop": "15px",
                    "textAlign": "center",
                    "fontSize": "14px",
                    "fontWeight": "500",
                    "minHeight": "20px",
                }
            ),
        ],
        style={
            "maxWidth": "420px",
            "margin": "0 auto",
            "padding": "40px 35px",
            "background": "white",
            "borderRadius": "16px",
            "boxShadow": "0 20px 60px rgba(0,0,0,0.12)",
            "animation": "fadeIn 0.5s ease-out",
        },
    )

app.layout = html.Div(
    [
        # Session storage for user state (changed to 'memory' so it doesn't persist across page refreshes)
        dcc.Store(id="session-store", storage_type="memory"),
        
        # Location for URL routing
        dcc.Location(id="url", refresh=False),

        dcc.Store(id="viewing-student", data=False),   
        
        # Main container
        html.Div(id="page-content", children=[login_page()], style={"width": "100%"}),
    ],
    style={
        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "backgroundSize": "400% 400%",
        "animation": "gradient 15s ease infinite",
        "minHeight": "100vh",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "padding": "20px",
    },
)


# Callback to control login message display
@app.callback(
    Output("login-message", "children"),
    Output("login-message", "style"),
    Input("session-store", "data"), 
    State("page-content", "children"),
    prevent_initial_call=False
)
def update_login_message(session_data, page_content):
    if session_data is None:
        return "", {"display": "none"}
    # Only show message if we have session data with an error
    if session_data.get("login_error"):
        return session_data["login_error"], {
            "marginTop": "15px",
            "textAlign": "center",
            "fontSize": "14px",
            "fontWeight": "500",
            "minHeight": "20px",
            "color": "#ef4444", 
        }
    
    # Default: empty message
    return "", {
        "marginTop": "15px",
        "textAlign": "center",
        "fontSize": "14px",
        "fontWeight": "500",
        "minHeight": "20px",
        "color": "#6b7280",
    }


@app.callback(
    Output("page-content", "children"),
    Output("session-store", "data"),
    Input("login-btn", "n_clicks"),
    State("role-toggle", "value"),
    State("username", "value"),
    State("password", "value"),
    State("semester-select", "value"),
    State("major-select", "value"),
    State("student-id-select", "value"),
    State("student-id-manual", "value"),
    State("student-password", "value"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def handle_navigation(
    login_clicks,
    role,
    username,
    password,
    semester,
    major,
    student_id_select,
    student_id_manual,
    student_password,
    session_data
):
    if not login_clicks:
        raise PreventUpdate
    if not session_data:
        session_data = {"logged_in": False}

    # ---------------- TEACHER LOGIN ----------------
    if role == "teacher":
        user = authenticate_teacher(username, password)
        if not user:
            session_data["login_error"] = "Invalid teacher credentials"
            return login_page(), session_data

        # Successful login - clear any errors
        session_data = {
            "logged_in": True,
            "role": "teacher",
            "major": user["major"]
        }
        session["logged_in"] = True
        session["role"] = "teacher"
        session["major"] = user["major"]

        return teacher_layout(user["major"]), session_data

    # ---------------- STUDENT LOGIN ----------------
    if role == "student":
        if not student_password:
            session_data["login_error"] = "Student password required"
            return login_page(), session_data

        if student_id_select:
            student_id = student_id_select
        elif student_id_manual and semester and major:
            student_id = f"{semester}-{major}-{student_id_manual}"
        else:
            session_data["login_error"] = "Please select or enter a valid student ID"
            return login_page(), session_data

        user = authenticate_student(student_id, student_password, get_student_by_id)
        if not user:
            session_data["login_error"] = "Invalid student ID or password"
            return login_page(), session_data

        # Successful login - clear any errors
        session_data = {
            "logged_in": True,
            "role": "student",
            "student_id": student_id
        }
        session["logged_in"] = True
        session["role"] = "student"
        session["student_id"] = student_id
        return student_layout(student_id), session_data

    return no_update, session_data


# Separate callback for logout button (uses pattern matching to avoid errors)
@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Input({"type": "logout-btn", "index": 0}, "n_clicks"),
    prevent_initial_call=True
)
def hard_logout(n_clicks):
    if not n_clicks:
        raise PreventUpdate

    session.clear()
    return login_page(), {"logged_in": False}


# Student profile includes a pattern id back button.
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("viewing-student", "data", allow_duplicate=True), 
    Input({"type": "back-to-teacher", "index": 0}, "n_clicks"),
    prevent_initial_call=True
)
def handle_back_to_teacher(n_clicks):
    if n_clicks:
        return "/teacher", False
    raise PreventUpdate


# Route to the correct page based on URL and session state.
@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    Output("session-store", "data", allow_duplicate=True),
    Input("url", "pathname"),
    State("session-store", "data"),
    prevent_initial_call="initial_duplicate"
)
def display_page(pathname, session_data):
    # Default route always shows the login page.
    if pathname == "/" or pathname is None:
        return login_page(), {"logged_in": False}

    # If the browser has no session state, go back to login.
    if not session_data:
        return login_page(), {"logged_in": False}

    # Teacher dashboard is only available after a successful teacher login.
    if (
        pathname == "/teacher"
        and session_data.get("logged_in") is True
        and session_data.get("role") == "teacher"
        and "major" in session_data
    ):
        return teacher_layout(session_data["major"]), session_data

    raise PreventUpdate


@app.callback(
    Output("semester-filter", "options"),
    Input("page-content", "children"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def load_teacher_filters(_, session_data):
    if not session_data or not session_data.get("logged_in") or session_data.get("role") != "teacher":
        raise PreventUpdate
    
    df = get_students_by_filters(major=session_data["major"])
    semesters = sorted(df["Program_Semester"].unique())
    options = [{"label": "All Semesters", "value": "ALL"}]
    options.extend([{"label": f"Semester {s}", "value": s} for s in semesters])
    return options


@app.callback(
    Output("teacher-summary", "children"),
    Output("risk-graph", "figure"),
    Output("students-table", "columns"),
    Output("students-table", "data"),
    Input("semester-filter", "value"),
    Input("url", "pathname"),
    State("session-store", "data"),
    State("viewing-student", "data"), 
    prevent_initial_call=False
)
def update_teacher_dashboard(semester, pathname, session_data, viewing_student):
    # While a student profile is open, we skip teacher dashboard refreshes.
    # This prevents unnecessary queries and avoids replacing the current page content.
    if viewing_student:
        raise PreventUpdate
    if not session_data or not session_data.get("logged_in") or session_data.get("role") != "teacher":
        raise PreventUpdate
    
    # Ignore URL triggers that are not the teacher route.
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    if "url" in triggered and pathname != "/teacher":
        raise PreventUpdate
    

    
    major = session_data["major"]
    
    # Load all students for the major, filter by semester if selected
    selected_semester = None if not semester or semester == "ALL" else semester
    df = get_students_by_filters(major=major, semester=selected_semester)

    if df.empty:
        empty_fig = px.scatter(
            title="Student Risk Landscape (GPA vs Attendance)"
        )
        empty_fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": "No students found for selected filter",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 16, "color": "#6b7280"},
                }
            ],
        )

        summary_cards = html.Div(
            [
                stat_card("Total Students", 0, "", ["#dbeafe", "#bfdbfe"]),
                stat_card("At Risk", 0, "", ["#fee2e2", "#fecaca"]),
                stat_card("Avg GPA", "N/A", "", ["#d1fae5", "#a7f3d0"]),
                stat_card("Avg Attendance", "N/A", "", ["#e9d5ff", "#d8b4fe"]),
            ],
            style={"display": "flex", "gap": "20px", "marginBottom": "30px"},
        )

        columns = [
            {"name": "Student Id", "id": "Student_ID", "presentation": "markdown"},
            {"name": "Full Name", "id": "Full_Name", "presentation": "markdown"},
            {"name": "Semester", "id": "Program_Semester"},
            {"name": "GPA", "id": "GPA"},
            {"name": "Attendance", "id": "Attendance_Percentage"},
            {"name": "Status", "id": "Academic_Status"},
            {"name": "Risk Probability", "id": "risk_probability_display"},
            {"name": "Pass Probability", "id": "pass_probability_display"},
            {"name": "Risk Category", "id": "risk_label"},
        ]
        return summary_cards, empty_fig, columns, []

    df = predict_risk(df)
    
    total_students = len(df)
    at_risk = df["risk_prediction"].sum()
    avg_gpa = round(df["GPA"].mean(), 2)
    avg_attendance = round(df["Attendance_Percentage"].mean(), 1)
    
    fig = px.scatter(
        df,
        x="Attendance_Percentage",
        y="GPA",
        color="risk_probability",
        color_continuous_scale="RdYlGn_r",
        size="risk_probability",
        size_max=15,
        hover_data=[
            "Full_Name",
            "risk_probability",
            "Academic_Status",
        ],
        title="Student Risk Landscape (GPA vs Attendance)",
        labels={
            "risk_probability": "Risk Probability",
            "Attendance_Percentage": "Attendance (%)",
            "GPA": "GPA",
        },
    )
    
    fig.update_traces(marker=dict(
        line=dict(width=1, color='white'),
        opacity=0.8,
        sizemin=8
    ))

    # Create display column with % but keep original for filtering
    df["risk_probability_display"] = (df["risk_probability"] * 100).round(2).astype(str) + "%"
    df["pass_probability_display"] = (df["pass_probability"] * 100).round(2).astype(str) + "%"
    display_df = df[
        [
            "Student_ID",
            "Full_Name",
            "Program_Semester",
            "GPA",
            "Attendance_Percentage",
            "Academic_Status",
            "risk_probability",
            "risk_probability_display",
            "pass_probability_display",
            "risk_label",
        ]
    ].copy()
    display_df["GPA"] = display_df["GPA"].round(2)
    display_df["Attendance_Percentage"] = display_df["Attendance_Percentage"].round(1).astype(str) + "%"
    columns = [
        {"name": "Student Id", "id": "Student_ID", "presentation": "markdown"},
        {"name": "Full Name", "id": "Full_Name", "presentation": "markdown"},
        {"name": "Semester", "id": "Program_Semester"},
        {"name": "GPA", "id": "GPA"},
        {"name": "Attendance", "id": "Attendance_Percentage"},
        {"name": "Status", "id": "Academic_Status"},
        {"name": "Risk Probability", "id": "risk_probability_display"},
        {"name": "Pass Probability", "id": "pass_probability_display"},
        {"name": "Risk Category", "id": "risk_label"},
    ]
    
    # Convert Student_ID and Full_Name to clickable - store original ID
    display_df["original_id"] = display_df["Student_ID"]
    display_df["id"] = display_df["original_id"]
    display_df["Student_ID"] = display_df["Student_ID"].apply(
        lambda x: f"[{x}](#)"
    )
    display_df["Full_Name"] = display_df.apply(
        lambda row: f"[{row['Full_Name']}](#)", axis=1
    )
    
    summary_cards = html.Div(
        [
            stat_card("Total Students", total_students, "", ["#dbeafe", "#bfdbfe"]),
            stat_card("At Risk", int(at_risk), "", ["#fee2e2", "#fecaca"]),
            stat_card("Avg GPA", avg_gpa, "", ["#d1fae5", "#a7f3d0"]),
            stat_card("Avg Attendance", f"{avg_attendance}%", "", ["#e9d5ff", "#d8b4fe"]),
        ],
        style={"display": "flex", "gap": "20px", "marginBottom": "30px"},
    )

    return summary_cards, fig, columns, display_df.to_dict("records")


# Add callback to handle row clicks in the table
@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    Output("viewing-student", "data"), 
    Input("students-table", "active_cell"),
    State("students-table", "data"),
    State("session-store", "data"),
    prevent_initial_call=True
)
def display_student_detail(active_cell, table_data, session_data):
    if not active_cell:
        raise PreventUpdate

    row = active_cell.get("row_id")
    if row is None:
        if not table_data:
            raise PreventUpdate
        selected = table_data[active_cell["row"]]
        row = selected.get("original_id")
    if row is None:
        raise PreventUpdate
    student_id = str(row)
    
    return student_layout(student_id, from_teacher=True), True


@app.callback(
    Output("student-id-select", "options"),
    Input("semester-select", "value"),
    Input("major-select", "value"),
    prevent_initial_call=True
)
def load_student_ids(semester_code, major_code):
    if not semester_code or not major_code:
        return []

    student_ids = get_sample_students_by_semester_major(
        semester_code,
        major_code,
        get_students_by_filters,
        limit=20
    )

    return [
        {"label": sid.split("-")[-1], "value": sid}
        for sid in student_ids
    ]


if __name__ == "__main__":
    app.run(debug=True)