from dash import html, dcc
import plotly.graph_objects as go
from utils.db_utils import get_student_by_id
from utils.model_utils import predict_risk

def info_item(label, value):
    return html.Div(
        [
            html.Div(label, style={"fontSize": "13px", "color": "#6b7280", "marginBottom": "4px"}),
            html.Div(str(value), style={"fontWeight": "600", "fontSize": "16px", "color": "#1f2937"}),
        ],
        style={"marginBottom": "16px"},
    )

def get_badge_color(level):
    level = str(level).strip().lower()
    if level in ['excellent', 'high']:
        return "bg-green-100 text-green-800"
    elif level in ['good', 'medium', 'average']:
        return "bg-blue-100 text-blue-800"
    else:
        return "bg-red-100 text-red-800"
    
def create_quiz_trend_graph(row):
    # Extract Quiz Scores 1-8 dynamically
    quiz_x = [f"Q{i}" for i in range(1, 9)]
    quiz_y = [row.get(f"Quiz_{i}_Score", 0) for i in range(1, 9)]

    fig = go.Figure()

    # Add the line with filled area
    fig.add_trace(go.Scatter(
        x=quiz_x, 
        y=quiz_y,
        mode='lines+markers',
        fill='tozeroy', # Fills area under line
        line=dict(color='#667eea', width=3, shape='spline'), # Smooth curve
        marker=dict(size=8, color='#764ba2', line=dict(width=2, color='white')),
        name='Quiz Score'
    ))

    fig.update_layout(
        title="Quiz Performance Trend",
        title_font=dict(size=16, color='#1f2937', family="Arial, sans-serif"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=20, t=40, b=40),
        yaxis=dict(
            range=[0, 105], 
            showgrid=True, 
            gridcolor='#f3f4f6',
            title="Score (%)"
        ),
        xaxis=dict(showgrid=False),
        hovermode="x unified"
    )
    return fig

def create_attendance_donut(row):
    # Data for Attendance
    attended = row['Classes_Attended']
    missed = row['Classes_Missed']
    
    # Colors: Green for Good, Red for Bad (using your theme colors)
    colors = ['#10b981', '#ef4444'] 

    fig = go.Figure(data=[go.Pie(
        labels=['Attended', 'Missed'],
        values=[attended, missed],
        hole=.7, # Makes it a Donut chart
        marker=dict(colors=colors),
        textinfo='none', # Hide text on slices to keep it clean
        hoverinfo='label+value+percent'
    )])

    # Add percentage text in the center of the donut
    percent = row['Attendance_Percentage']
    
    fig.update_layout(
        title="Attendance Breakdown",
        title_font=dict(size=16, color='#1f2937', family="Arial, sans-serif"),
        annotations=[dict(text=f"{percent:.2f}%", x=0.5, y=0.5, font_size=24, showarrow=False, font_weight='bold')],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    return fig
def student_layout(student_id, from_teacher=False):
    df = get_student_by_id(student_id)
    if df.empty:
        return html.Div(
           "Student not found",
            style={
               "textAlign": "center",
               "padding": "40px",
               "color": "#ef4444",
               "fontSize": "18px",
            }
        )
    
    df = predict_risk(df)
    row = df.iloc[0]
    
    # Determine risk level and colors
    risk_prob = float(row["risk_probability"]) * 100
    pass_prob = float(row["pass_probability"]) * 100
    risk_label = row["risk_label"]
    if risk_prob < 25:
        risk_color = "#10b981"
    elif risk_prob < 50:
        risk_color = "#f59e0b"
    elif risk_prob < 75:
        risk_color = "#ef4444"
    else:
        risk_color = "#7f1d1d"
    
    # Build the layout with conditional back button and logout button
    children = []
    
    # Add back button if coming from teacher view
    if from_teacher:
        children.append(
            html.Button(
               "← Back to Dashboard",
                id={"type": "back-to-teacher", "index": 0},
                style={
                   "background": "transparent",
                   "border": "none",
                   "color": "#4f46e5",
                   "fontSize": "14px",
                   "fontWeight": "600",
                   "cursor": "pointer",
                   "marginBottom": "20px",
                }
            )
        )
    else:
        # Add logout button for student login
        children.append(
            html.Button(
               "Logout",
                id={"type": "logout-btn", "index": 0},
                style={
                   "position": "fixed",
                   "top": "20px",
                   "right": "20px",
                   "padding": "10px 20px",
                   "background": "#ef4444",
                   "color": "white",
                   "border": "none",
                   "borderRadius": "8px",
                   "cursor": "pointer",
                   "zIndex": "1000",
                   "fontSize": "14px",
                   "fontWeight": "600",
                }
            )
        )
    
    # Profile content
    children.extend([
        # Header with gradient
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            f"{'Student Profile: ' if from_teacher else 'Welcome back, '}{row['Full_Name']}{'!' if not from_teacher else ' '}",
                            style={
                               "color": "white",
                               "margin": "0",
                               "fontSize": "28px",
                               "fontWeight": "700",
                            }
                        ),
                        html.P(
                            f"{row['Major']} • Semester {row['Program_Semester']} • Student ID: {row['Student_ID']}",
                            style={
                               "color": "rgba(255,255,255,0.9)",
                               "margin": "8px 0 0 0",
                               "fontSize": "16px",
                            }
                        ),
                    ]
                ),
            ],
            id=f"profile-header-{student_id}",
            style={
               "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
               "padding": "40px",
               "borderRadius": "16px",
               "marginBottom": "30px",
               "boxShadow": "0 10px 40px rgba(102, 126, 234, 0.3)",
            }
        ),
        
        # Academic Overview Cards
        html.Div(
            [
                html.Div(
                    [
                        html.Div("", style={"fontSize": "32px", "marginBottom": "8px"}),
                        html.Div("GPA", style={"fontSize": "13px", "color": "#6b7280"}),
                        html.Div(
                            str(row["GPA"]),
                            style={"fontSize": "32px", "fontWeight": "700", "color": "#1f2937", "marginTop": "4px"}
                        ),
                    ],
                    style={
                       "background": "white",
                       "padding": "24px",
                       "borderRadius": "12px",
                       "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                       "flex": "1",
                       "textAlign": "center",
                    }
                ),
                html.Div(
                    [
                        html.Div("", style={"fontSize": "32px", "marginBottom": "8px"}),
                        html.Div("Academic Status", style={"fontSize": "13px", "color": "#6b7280"}),
                        html.Div(
                            row["Academic_Status"],
                            style={"fontSize": "18px", "fontWeight": "600", "color": "#1f2937", "marginTop": "8px"}
                        ),
                    ],
                    style={
                       "background": "white",
                       "padding": "24px",
                       "borderRadius": "12px",
                       "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                       "flex": "1",
                       "textAlign": "center",
                    }
                ),
            ],
            id=f"overview-cards-{student_id}",
            style={
               "display": "flex",
               "gap": "20px",
               "marginBottom": "30px",
            }
        ),
        
        # Risk Gauge
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                           "Your Academic Risk Level",
                            style={"marginTop": "0", "marginBottom": "20px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}
                        ),
                        dcc.Graph(
                            id=f"risk-gauge-{student_id}",
                            figure=go.Figure(
                                go.Indicator(
                                    mode="gauge+number",
                                    value=risk_prob,
                            title={"text": f"{risk_label} Risk", "font": {"size": 24, "color": risk_color}},
                                    number={"suffix": "%", "font": {"size": 48}},
                                    gauge={
                                       "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#e5e7eb"},
                                       "bar": {"color": risk_color, "thickness": 0.75},
                                       "bgcolor": "white",
                                       "borderwidth": 2,
                                       "bordercolor": "#e5e7eb",
                                       "steps": [
                                            {"range": [0, 25], "color": "#d1fae5"},
                                            {"range": [25, 50], "color": "#fef3c7"},
                                            {"range": [50, 75], "color": "#fee2e2"},
                                            {"range": [75, 100], "color": "#fecaca"},
                                        ],
                                       "threshold": {
                                           "line": {"color": risk_color, "width": 4},
                                           "thickness": 0.75,
                                           "value": risk_prob
                                        }
                                    }
                                )
                            ).update_layout(
                                height=300,
                                margin=dict(l=20, r=20, t=40, b=20),
                                paper_bgcolor="white",
                                font={"family": "Arial, sans-serif"}
                            ),
                            config={'displayModeBar': False, 'staticPlot': True}
                        ),
                    ]
                ),
            ],
            id=f"risk-gauge-section-{student_id}",
            style={
               "background": "white",
               "padding": "30px",
               "borderRadius": "12px",
               "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
               "marginBottom": "30px",
            }
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Pass Probability", style={"fontSize": "13px", "color": "#6b7280"}),
                        html.Div(f"{pass_prob:.2f}%", style={"fontSize": "24px", "fontWeight": "700", "color": "#1f2937"}),
                    ],
                    style={"flex": "1", "background": "white", "padding": "20px", "borderRadius": "12px", "boxShadow": "0 4px 20px rgba(0,0,0,0.08)", "textAlign": "center"},
                ),
                html.Div(
                    [
                        html.Div("Risk Category", style={"fontSize": "13px", "color": "#6b7280"}),
                        html.Div(risk_label, style={"fontSize": "24px", "fontWeight": "700", "color": risk_color}),
                    ],
                    style={"flex": "1", "background": "white", "padding": "20px", "borderRadius": "12px", "boxShadow": "0 4px 20px rgba(0,0,0,0.08)", "textAlign": "center"},
                ),
            ],
            style={"display": "flex", "gap": "20px", "marginBottom": "30px"},
        ),
        
        # Courses Enrolled
        html.Div(
            [
                html.H3(" Courses Enrolled", style={"marginTop": "0", "marginBottom": "16px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}),
                html.P(
                    row["Courses"],
                    style={"color": "#4b5563", "lineHeight": "1.6", "margin": "0"}
                ),
            ],
            id=f"courses-section-{student_id}",
            style={
               "background": "white",
               "padding": "24px",
               "borderRadius": "12px",
               "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
               "marginBottom": "30px",
            },
        ),
        
        # Detailed analytics
        html.Div(
            [
                html.H3(" Detailed Performance Analytics", style={"marginTop": "0", "marginBottom": "24px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}),
                
                html.Div(
                    [
                        # Left Column: Quiz Trend Graph
                        html.Div(
                            dcc.Graph(
                                figure=create_quiz_trend_graph(row),
                                config={'displayModeBar': False}
                            ),
                            style={
                               "flex": "2", # Takes up 2/3rds of space
                               "background": "white",
                               "borderRadius": "12px",
                               "padding": "10px",
                               "boxShadow": "0 2px 10px rgba(0,0,0,0.05)"
                            }
                        ),

                        # Right Column: Attendance & Exams
                        html.Div(
                            [
                                # Attendance Donut
                                html.Div(
                                    dcc.Graph(
                                        figure=create_attendance_donut(row),
                                        config={'displayModeBar': False}
                                    ),
                                    style={"marginBottom": "20px", "height": "300px"}
                                ),
                                
                                # Mini Stats for Exams (Midterm vs Final)
                                html.Div(
                                    [
                                        html.Div([
                                            html.Div("Midterm", style={"fontSize": "12px", "color": "#6b7280"}),
                                            html.Div(f"{row['Midterm_Score']}", style={"fontSize": "20px", "fontWeight": "700", "color": "#4f46e5"})
                                        ], style={"textAlign": "center", "background": "#eef2ff", "padding": "15px", "borderRadius": "8px", "flex": "1"}),
                                        
                                        html.Div([
                                            html.Div("Final", style={"fontSize": "12px", "color": "#6b7280"}),
                                            html.Div(f"{row['Final_Score']}", style={"fontSize": "20px", "fontWeight": "700", "color": "#7c3aed"})
                                        ], style={"textAlign": "center", "background": "#f5f3ff", "padding": "15px", "borderRadius": "8px", "flex": "1"}),
                                    ],
                                    style={"display": "flex", "gap": "10px"}
                                )
                            ],
                            style={
                               "flex": "1", # Takes up 1/3rd of space
                               "background": "white",
                               "borderRadius": "12px",
                               "padding": "20px",
                               "boxShadow": "0 2px 10px rgba(0,0,0,0.05)",
                               "display": "flex",
                               "flexDirection": "column",
                               "justifyContent": "space-between"
                            }
                        ),
                    ],
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}
                ),
            ],
            style={
               "marginBottom": "30px",
            },
        ),
        
        # Engagement and habits
        html.Div(
            [
                html.H3(" Engagement & Habits", style={"marginTop": "30px", "marginBottom": "20px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}),
                html.Div(
                    [
                        # Study Habits Badge
                        html.Div([
                            html.Span("Study Habits", style={"color": "#6b7280", "fontSize": "14px", "display": "block", "marginBottom": "8px"}),
                            html.Span(f"{row.get('Study_Habits', 'N/A')}", 
                                      className=f"px-3 py-1 rounded-full font-semibold text-sm {get_badge_color(row.get('Study_Habits', ''))}")
                        ], style={"flex": "1", "background": "white", "padding": "20px", "borderRadius": "12px", "boxShadow": "0 2px 10px rgba(0,0,0,0.05)", "textAlign": "center"}),

                        # Participation Badge
                        html.Div([
                            html.Span("Class Participation", style={"color": "#6b7280", "fontSize": "14px", "display": "block", "marginBottom": "8px"}),
                            html.Span(f"{row.get('Class_Participation', 'N/A')}", 
                                      className=f"px-3 py-1 rounded-full font-semibold text-sm {get_badge_color(row.get('Participation_Level', ''))}")
                        ], style={"flex": "1", "background": "white", "padding": "20px", "borderRadius": "12px", "boxShadow": "0 2px 10px rgba(0,0,0,0.05)", "textAlign": "center"}),

                        # Assignments Progress
                        html.Div([
                            html.Span(f"Assignments Completed: {row.get('Assignments_Completed', 0)} / {row.get('Total_Assignments', 0)}", 
                                      style={"color": "#6b7280", "fontSize": "14px", "display": "block", "marginBottom": "8px", "fontWeight": "500"}),
                            html.Div([
                                html.Div(style={
                                   "width": f"{min(100, (row.get('Assignments_Completed', 0) / max(row.get('Total_Assignments', 1), 1)) * 100)}%", 
                                   "background": "#4f46e5", 
                                   "height": "100%", 
                                   "borderRadius": "999px"
                                })
                            ], style={"background": "#e5e7eb", "height": "12px", "borderRadius": "999px", "width": "100%"})
                        ], style={"flex": "2", "background": "white", "padding": "20px 20px 40px 20px", "borderRadius": "12px", "boxShadow": "0 2px 10px rgba(0,0,0,0.05)"}),
                    ],
                    style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}
                )
            ],
                style={
       "background": "#f9fafb",
       "padding": "30px",
       "borderRadius": "12px",
       "marginBottom": "30px",   # <-- this is the key spacing fix
    }
        ),
        # Risk Factors and Recommendations
        (
            html.Div(
                [
                    html.Div(
                        [
                            html.H3("️ Top Contributing Risk Factors", style={"marginTop": "0", "marginBottom": "16px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}),
                            html.Ul(
                                [
                                    html.Li(
                                        (
                                            f"{str(item.get('label', item.get('feature', ''))).replace('_', ' ')}"
                                            + (
                                                f" ({float(item.get('importance', 0)):.2%})"
                                                if float(item.get("importance", 0) or 0) > 0
                                                else ""
                                            )
                                            + (f". {item.get('evidence')}" if item.get('evidence') else "")
                                        ),
                                        style={"marginBottom": "8px", "color": "#4b5563", "lineHeight": "1.6"},
                                    )
                                    for item in row["top_features"]
                                ],
                                style={"paddingLeft": "20px", "margin": "0"}
                            ) if row["top_features"] else html.P("No significant risk factors identified! ", style={"color": "#10b981", "fontWeight": "500"}),
                        ],
                        style={
                           "background": "white",
                           "padding": "24px",
                           "borderRadius": "12px",
                           "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                           "flex": "1",
                        }
                    ),
                    html.Div(
                        [
                            html.H3(" Recommended Actions", style={"marginTop": "0", "marginBottom": "16px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}),
                            html.Ul(
                                [html.Li(r, style={"marginBottom": "8px", "color": "#4b5563", "lineHeight": "1.6"}) for r in row["recommendations"]],
                                style={"paddingLeft": "20px", "margin": "0"}
                            ),
                        ],
                        style={
                           "background": "white",
                           "padding": "24px",
                           "borderRadius": "12px",
                           "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                           "flex": "1",
                        }
                    ),
                ],
                style={"display": "flex", "gap": "20px", "marginBottom": "30px"}
            )
            if not (risk_prob < 25 and pass_prob > 75)
            else html.Div(
                [
                    html.H3(" Risk Outlook", style={"marginTop": "0", "marginBottom": "12px", "color": "#1f2937", "fontSize": "20px", "fontWeight": "600"}),
                    html.P(
                        "Your current performance indicates low academic risk. Keep maintaining your current study and attendance habits.",
                        style={"color": "#166534", "fontWeight": "500", "margin": "0"},
                    ),
                ],
                style={
                    "background": "#ecfdf5",
                    "padding": "24px",
                    "borderRadius": "12px",
                    "border": "1px solid #bbf7d0",
                    "marginBottom": "30px",
                },
            )
        ),
    ])
    
    return html.Div(
        children,
        id=f"student-profile-{student_id}",
        style={
           "maxWidth": "1000px",
           "margin": "0 auto",
           "padding": "30px",
           "background": "#f9fafb",
           "minHeight": "100vh",
        },
    )