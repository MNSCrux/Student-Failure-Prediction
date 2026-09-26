from dash import html, dcc, dash_table

def stat_card(title, value, icon, gradient):
    return html.Div(
        [
            html.Div(
                icon,
                style={
                   "fontSize": "32px",
                   "marginBottom": "12px",
                }
            ),
            html.Div(title, style={"fontSize": "13px", "color": "#374151", "marginBottom": "8px", "fontWeight": "500"}),
            html.Div(
                str(value),
                style={
                   "fontSize": "32px",
                   "fontWeight": "700",
                   "color": "#1f2937",
                },
            ),
        ],
        style={
           "background": f"linear-gradient(135deg, {gradient[0]}, {gradient[1]})",
           "padding": "24px",
           "borderRadius": "12px",
           "flex": "1",
           "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
           "textAlign": "center",
        },
    )

def teacher_layout(major):
    return html.Div(
        [
            # Store teacher major for callbacks
            dcc.Store(id="teacher-major", data=major),
            
            # Logout button
            html.Button(
               "Logout",
                id={"type": "logout-btn", "index": 0},
                style={
                   "display": "block",
                   "marginLeft": "auto",
                   "marginBottom": "16px",
                   "padding": "10px 20px",
                   "background": "#ef4444",
                   "color": "white",
                   "border": "none",
                   "borderRadius": "8px",
                   "cursor": "pointer",
                   "fontSize": "14px",
                   "fontWeight": "600",
                }
            ),
            
            # Header
            html.Div(
                [
                    html.H2(
                        f"{major} Teacher Dashboard ",
                        style={
                           "color": "white",
                           "margin": "0",
                           "fontSize": "32px",
                           "fontWeight": "700",
                        }
                    ),
                    html.P(
                       "Monitor student performance and identify at-risk students",
                        style={
                           "color": "rgba(255,255,255,0.9)",
                           "margin": "8px 0 0 0",
                           "fontSize": "16px",
                        }
                    ),
                ],
                style={
                   "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                   "padding": "40px",
                   "borderRadius": "16px",
                   "marginBottom": "30px",
                   "boxShadow": "0 10px 40px rgba(102, 126, 234, 0.3)",
                }
            ),
            
            # Filters
            html.Div(
                [
                    html.Label(
                       "Filter by Semester",
                        style={
                           "fontSize": "14px",
                           "fontWeight": "600",
                           "color": "#374151",
                           "marginBottom": "8px",
                           "display": "block",
                        }
                    ),
                    dcc.Dropdown(
                        id="semester-filter",
                        options=[{"label": "All Semesters", "value": "ALL"}],
                        value="ALL",
                        placeholder="All Semesters (default)",
                        clearable=True,
                        style={
                           "borderRadius": "8px",
                        }
                    ),
                ],
                style={
                   "background": "white",
                   "padding": "20px",
                   "borderRadius": "12px",
                   "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                   "marginBottom": "30px",
                   "maxWidth": "400px",
                }
            ),
            
            # Summary Cards
            dcc.Loading(
                id="teacher-dashboard-loading",
                type="circle",
                children=html.Div(
                    [
                        # Summary Cards
                        html.Div(
                            id="teacher-summary",
                            style={"marginBottom": "30px"},
                        ),

                        # Risk Graph
                        html.Div(
                            [
                                dcc.Graph(
                                    id="risk-graph",
                                    config={"displayModeBar": False},
                                    style={"borderRadius": "12px"},
                                ),
                            ],
                            style={
                                "background": "white",
                                "padding": "24px",
                                "borderRadius": "12px",
                                "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                                "marginBottom": "30px",
                            },
                        ),

                        # Students Table
                        html.Div(
                            [
                                html.H3(
                                    " Student Details",
                                    style={
                                        "marginTop": "0",
                                        "marginBottom": "20px",
                                        "color": "#1f2937",
                                        "fontSize": "20px",
                                        "fontWeight": "600",
                                    },
                                ),
                                dash_table.DataTable(
                                    id="students-table",
                                    page_size=20,
                                    page_action="native",
                                    sort_action="native",
                                    filter_action="none",
                                    row_selectable=False,
                                    markdown_options={"link_target": "_self"},
                                    style_table={
                                        "overflowX": "auto",
                                        "width": "100%",
                                        "borderRadius": "8px",
                                    },
                                    style_cell={
                                        "minWidth": "90px",
                                        "maxWidth": "150px",
                                        "whiteSpace": "nowrap",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis",
                                        "textAlign": "left",
                                        "padding": "10px",
                                        "fontSize": "13px",
                                        "fontFamily": "Arial, sans-serif",
                                    },
                                    style_header={
                                        "backgroundColor": "#1f2937",
                                        "color": "white",
                                        "fontWeight": "600",
                                        "border": "none",
                                        "padding": "16px 12px",
                                    },
                                    style_data={
                                        "border": "none",
                                        "borderBottom": "1px solid #e5e7eb",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"filter_query": "{risk_probability} >= 0.6"},
                                            "backgroundColor": "#fee2e2",
                                            "color": "#991b1b",
                                            "fontWeight": "500",
                                        },
                                        {
                                            "if": {"filter_query": "{risk_probability} >= 0.3 && {risk_probability} < 0.6"},
                                            "backgroundColor": "#fef3c7",
                                            "color": "#92400e",
                                            "fontWeight": "500",
                                        },
                                        {
                                            "if": {"state": "selected"},
                                            "backgroundColor": "#dbeafe",
                                            "border": "1px solid #3b82f6",
                                        },
                                    ],
                                    css=[
                                        {
                                            "selector": "a",
                                            "rule": "color: #4f46e5; text-decoration: none; font-weight: 500;",
                                        },
                                        {
                                            "selector": "a:hover",
                                            "rule": "color: #6366f1; text-decoration: underline;",
                                        },
                                    ],
                                ),
                            ],
                            style={
                                "background": "white",
                                "padding": "24px",
                                "borderRadius": "12px",
                                "boxShadow": "0 4px 20px rgba(0,0,0,0.08)",
                            },
                        ),
                    ]
                ),
            ),
        ],
        style={
           "maxWidth": "90vw",
           "width": "90vw",
           "margin": "0 auto",
           "padding": "16px 20px",
           "background": "#f9fafb",
           "minHeight": "100vh",
        },
    )