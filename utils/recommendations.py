def get_risk_label(risk_prob):
    if risk_prob < 0.25:
        return "Low"
    if risk_prob < 0.5:
        return "Medium"
    if risk_prob < 0.75:
        return "High"
    return "Critical"


def generate_recommendations(risk_prob, risk_factors):
    """
    Generate recommendations from *confirmed* risk factors.
    This avoids misleading output from RF importance alone.
    """
    label = get_risk_label(risk_prob)
    recommendations = []
    added_keys = set()

    def add_rec(key: str, text: str):
        key = str(key or "").strip().lower()
        if not key:
            key = text.strip().lower()
        if key in added_keys:
            return
        added_keys.add(key)
        recommendations.append(text)

    # Aggregate quiz recommendations so we do not output one per quiz.
    quiz_nums_needing_help = []
    quiz_consistency_risk = False

    for f in risk_factors or []:
        f_type = str(f.get("type", "")).strip().lower()
        evidence = f.get("evidence")
        value = f.get("value")
        threshold = f.get("threshold")
        quiz_num = f.get("quiz_num")
        category = f.get("category")
        score = f.get("score")

        if f_type == "attendance":
            add_rec(
                "attendance",
                "Attendance needs attention. Set a weekly attendance goal, use reminders, and identify one concrete reason for any missed class (then remove it next week).",
            )

        elif f_type == "academic_status":
            add_rec(
                "academic_status",
                "Academic standing needs urgent support. Meet your course instructor or advisor this week to agree on the minimum targets for the next two weeks.",
            )

        elif f_type == "quiz":
            if quiz_num is not None:
                quiz_nums_needing_help.append(int(quiz_num))
            else:
                quiz_consistency_risk = True

        elif f_type == "quiz_aggregate":
            quiz_consistency_risk = True

        elif f_type == "midterm":
            add_rec(
                "midterm",
                "Midterm performance is a risk. Build a midterm focused plan: (1) summary sheet of core concepts, (2) daily mixed practice, (3) timed past paper questions twice per week.",
            )

        elif f_type == "final":
            add_rec(
                "final",
                "Final exam preparation needs attention. Start early with a structured plan and add final style practice questions every week.",
            )

        elif f_type == "assignment_completion":
            add_rec(
                "assignments",
                "Assignments are behind schedule. Make a weekly submission checklist, clear overdue work first, and book two fixed catch up blocks each week.",
            )

        elif f_type == "gpa":
            if isinstance(value, (int, float)) and isinstance(threshold, (int, float)):
                add_rec(
                    "gpa",
                    "GPA needs support. Meet an advisor or tutor, then follow a simple weekly study routine (short daily sessions plus one longer weekend review).",
                )
            else:
                add_rec(
                    "gpa",
                    "GPA needs support. Meet an advisor or tutor and follow a consistent weekly study routine.",
                )

        elif f_type == "class_participation":
            if label != "Low":
                if score is not None:
                    add_rec(
                        "participation",
                        "Class participation is low. Improve engagement by asking one question per class and writing a 3 bullet summary after each lecture.",
                    )
                else:
                    add_rec(
                        "participation",
                        "Class participation is low. Improve engagement by asking one question per class and writing a 3 bullet summary after each lecture.",
                    )

        elif f_type == "study_habits":
            if label != "Low":
                if category == "Poor":
                    add_rec(
                        "study_habits",
                        "Study habits need a reset. Use short daily sessions, keep them scheduled, and track completion each day.",
                    )
                elif category == "Needs Improvement":
                    add_rec(
                        "study_habits",
                        "Study habits need improvement. Switch to consistent review (spaced practice) and do practice quizzes before assessments.",
                    )
                else:
                    add_rec(
                        "study_habits",
                        "Improve your study habits by using a consistent weekly routine and practice based revision.",
                    )

        else:
            # Unknown factor type: fall back to evidence-only recommendation.
            if evidence:
                recommendations.append(f"Address risk: {evidence}")

    # Add at most ONE quiz recommendation even if multiple quiz factors exist.
    quiz_nums_needing_help = sorted(set([n for n in quiz_nums_needing_help if isinstance(n, int)]))
    if quiz_nums_needing_help or quiz_consistency_risk:
        if quiz_nums_needing_help:
            quiz_list = ", ".join([f"Quiz {n}" for n in quiz_nums_needing_help])
            add_rec(
                "quizzes",
                f"Quiz performance needs a reset. Focus on {quiz_list} topics (notes and worked examples), then do targeted timed practice questions and review every mistake using an error log.",
            )
        else:
            add_rec(
                "quizzes",
                "Quiz consistency is a risk. Use a timed revision schedule, do extra practice quizzes each week, and keep an error log (topic, mistake, fix).",
            )

    if not recommendations:
        if label in ["High", "Critical"]:
            add_rec("generic_high", "Schedule advisor follow up and use focused weekly progress tracking.")
        elif label == "Medium":
            add_rec("generic_medium", "Keep consistent study and attendance habits with weekly self review.")
        else:
            add_rec("generic_low", "Maintain current performance with regular practice and attendance discipline.")

    if label in ["High", "Critical"]:
        # If probation is already flagged, keep the support message but avoid repeating the same idea twice.
        add_rec(
            "support_now",
            "Immediate support: book office hours or tutoring this week, bring your quiz attempts, and ask for the exact topics and skills to prioritize.",
        )
        add_rec(
            "two_week_plan",
            "Two week recovery plan: Week 1 rebuild fundamentals (daily timed practice and an error log). Week 2 intensify (mixed practice, two timed mini mocks, and review).",
        )

    # If we only produced a small number of actions, add one general routine to keep the advice useful.
    if len(recommendations) < 2 and label in ["Medium", "High", "Critical"]:
        add_rec(
            "weekly_routine",
            "General routine: 45 to 60 minutes daily (practice first, then review), plus one longer weekly session to consolidate notes and redo missed questions.",
        )

    # Stable deterministic order and no duplicates.
    return recommendations
