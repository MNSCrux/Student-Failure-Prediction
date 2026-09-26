import joblib
import numpy as np

from utils.recommendations import generate_recommendations, get_risk_label

MODEL_PATH = "Model/student_risk_random_forest.pkl"
model = joblib.load(MODEL_PATH)

TARGET_COLUMN = "at_risk_flag"
EXCLUDED_FEATURE_PREFIXES = (
    "Age",
    "Gender_",
    "Major_",
    "Program_Semester",
    "Academic_Year",
    "Attendance_Category_",
    "Courses_",
)
ALLOWED_RISK_FEATURES = {
    "Attendance_Percentage",
    "Classes_Attended",
    "Classes_Missed",
    "Assignment_Completion_Percentage",
    "Assignments_Completed",
    "Avg_Quiz_Score",
    "Quiz_Pass_Rate",
    "Midterm_Score",
    "Final_Score",
    "GPA",
    "Quiz_1_Score",
    "Quiz_2_Score",
    "Quiz_3_Score",
    "Quiz_4_Score",
    "Quiz_5_Score",
    "Quiz_6_Score",
    "Quiz_7_Score",
    "Quiz_8_Score",
    # One-hot encoded categorical drivers (via the model preprocessor)
    "Class_Participation_Low",
    "Class_Participation_Medium",
    "Class_Participation_High",
    "Study_Habits_Poor",
    "Study_Habits_Needs Improvement",
    "Study_Habits_Consistent",
    "Study_Habits_Highly Consistent",
}

# Thresholds used to turn model signals into plain risk factors.
ATTENDANCE_RISK_THRESHOLD_PCT = 75.0
QUIZ_RISK_THRESHOLD_PCT = 60.0
# Exam threshold used for Midterm and Final.
EXAM_RISK_THRESHOLD_PCT = 60.0
ASSIGNMENT_COMPLETION_RISK_THRESHOLD_PCT = 80.0
GPA_RISK_THRESHOLD = 2.5
QUIZ_PASS_RATE_RISK_THRESHOLD_PCT = 80.0


def _safe_float(v):
    try:
        if v is None:
            return None
        if isinstance(v, (int, float, np.number)):
            if np.isnan(v):
                return None
            return float(v)
        return float(str(v).strip())
    except Exception:
        return None


def _clean_feature_name(name):
    cleaned = str(name).replace("num__", "").replace("cat__", "")
    return cleaned


def _risk_signal(feature_name, row):
    """Return [0,1] risk signal where higher means weaker performance."""
    lname = str(feature_name).lower()

    # The model uses one hot encoded categories, but the DB row stores the original text.
    if lname.startswith("class_participation_"):
        category = str(feature_name).split("Class_Participation_", 1)[1].strip()
        raw = str(row.get("Class_Participation", "")).strip()
        if raw != category:
            return 0.0
        # Higher value means higher risk contribution.
        if category == "Low":
            return 1.0
        if category == "Medium":
            return 0.5
        return 0.0

    if lname.startswith("study_habits_"):
        category = str(feature_name).split("Study_Habits_", 1)[1].strip()
        raw = str(row.get("Study_Habits", "")).strip()
        if raw != category:
            return 0.0
        if category == "Poor":
            return 1.0
        if category == "Needs Improvement":
            return 0.65
        if category == "Consistent":
            return 0.25
        return 0.05

    # Numeric drivers map directly to DB columns.
    value = row.get(feature_name, None)
    if value is None or not isinstance(value, (int, float, np.number)) or np.isnan(value):
        return 0.0

    v = float(value)

    if "gpa" in lname:
        return max(0.0, min(1.0, (4.0 - v) / 4.0))

    if lname == "classes_missed":
        total = float(row.get("Total_Classes", 0) or 0)
        denom = total if total > 0 else 1.0
        return max(0.0, min(1.0, v / denom))

    if lname == "classes_attended":
        total = float(row.get("Total_Classes", 0) or 0)
        if total <= 0:
            return 0.0
        attendance_ratio = v / total
        return max(0.0, min(1.0, 1.0 - attendance_ratio))

    if lname == "assignments_completed":
        total = float(row.get("Total_Assignments", 0) or 0)
        if total <= 0:
            return 0.0
        completion_ratio = v / total
        return max(0.0, min(1.0, 1.0 - completion_ratio))

    if (
        "percentage" in lname
        or "score" in lname
        or "rate" in lname
        or "quiz_" in lname
        or "midterm" in lname
        or "final" in lname
    ):
        return max(0.0, min(1.0, (100.0 - v) / 100.0))

    return 0.0


def _confirm_risk_factor(feature_name, row, importance, risk_label):
    """
    Confirm whether a candidate RF feature is a *real* risk for this specific student,
    based on the student's actual DB values and explicit thresholds.
    """

    def make_item(label, evidence=None, value=None, threshold=None, extra=None):
        item = {
            "feature": feature_name,
            "importance": float(importance),
            "label": label,
            "evidence": evidence,
        }
        if value is not None:
            item["value"] = value
        if threshold is not None:
            item["threshold"] = threshold
        if extra:
            item.update(extra)
        return item

    # Attendance (validate via Attendance_Percentage even if the RF driver was Classes_Attended/Classes_Missed)
    if feature_name in {"Attendance_Percentage", "Classes_Attended", "Classes_Missed"}:
        val = _safe_float(row.get("Attendance_Percentage"))
        if val is None:
            return None
        if val < ATTENDANCE_RISK_THRESHOLD_PCT:
            return make_item(
                "Attendance",
                evidence="Below target",
                value=val,
                threshold=ATTENDANCE_RISK_THRESHOLD_PCT,
            )
        return None

    # Quizzes (individual)
    if str(feature_name).startswith("Quiz_") and str(feature_name).endswith("_Score"):
        quiz_num = None
        try:
            quiz_num = int(str(feature_name).split("Quiz_", 1)[1].split("_Score", 1)[0])
        except Exception:
            pass

        if quiz_num is None:
            return None

        col = f"Quiz_{quiz_num}_Score"
        val = _safe_float(row.get(col))
        if val is None:
            return None
        if val < QUIZ_RISK_THRESHOLD_PCT:
            return make_item(
                f"Quiz {quiz_num} score",
                evidence="Below target",
                value=val,
                threshold=QUIZ_RISK_THRESHOLD_PCT,
                extra={"quiz_num": quiz_num},
            )
        return None

    # Quiz aggregates
    if feature_name == "Avg_Quiz_Score":
        val = _safe_float(row.get("Avg_Quiz_Score"))
        if val is None:
            return None
        if val < QUIZ_RISK_THRESHOLD_PCT:
            return make_item(
                "Average quiz score",
                evidence="Below target",
                value=val,
                threshold=QUIZ_RISK_THRESHOLD_PCT,
            )
        return None

    if feature_name == "Quiz_Pass_Rate":
        val = _safe_float(row.get("Quiz_Pass_Rate"))
        if val is None:
            return None
        if val < QUIZ_PASS_RATE_RISK_THRESHOLD_PCT:
            return make_item(
                "Quiz pass rate",
                evidence="Inconsistent quiz performance",
                value=val,
                threshold=QUIZ_PASS_RATE_RISK_THRESHOLD_PCT,
            )
        return None

    # Exams
    if feature_name == "Midterm_Score":
        val = _safe_float(row.get("Midterm_Score"))
        if val is None:
            return None
        if val < EXAM_RISK_THRESHOLD_PCT:
            return make_item(
                "Midterm score",
                evidence="Below target",
                value=val,
                threshold=EXAM_RISK_THRESHOLD_PCT,
            )
        return None

    if feature_name == "Final_Score":
        val = _safe_float(row.get("Final_Score"))
        if val is None:
            return None
        if val < EXAM_RISK_THRESHOLD_PCT:
            return make_item(
                "Final score",
                evidence="Below target",
                value=val,
                threshold=EXAM_RISK_THRESHOLD_PCT,
            )
        return None

    # For assignments, always validate using the overall completion percentage.
    if feature_name in {"Assignment_Completion_Percentage", "Assignments_Completed"}:
        val = _safe_float(row.get("Assignment_Completion_Percentage"))
        if val is None:
            return None
        if val < ASSIGNMENT_COMPLETION_RISK_THRESHOLD_PCT:
            return make_item(
                "Assignment completion",
                evidence="Behind schedule",
                value=val,
                threshold=ASSIGNMENT_COMPLETION_RISK_THRESHOLD_PCT,
            )
        return None

    # GPA
    if feature_name == "GPA":
        val = _safe_float(row.get("GPA"))
        if val is None:
            return None
        if val < GPA_RISK_THRESHOLD:
            return make_item(
                "GPA",
                evidence="Below target",
                value=val,
                threshold=GPA_RISK_THRESHOLD,
            )
        return None

    # Categorical factors are only confirmed when the raw DB category matches.
    if str(feature_name).startswith("Class_Participation_"):
        # Keep these habit factors out of the "low risk" view to avoid noisy feedback.
        if risk_label == "Low":
            return None

        category = str(feature_name).split("Class_Participation_", 1)[1].strip()
        raw = str(row.get("Class_Participation", "")).strip()

        # Only "Low" participation is treated as a risk factor.
        if raw != category or category != "Low":
            return None

        score = _safe_float(row.get("Participation_Score"))
        if score is not None:
            return make_item(
                "Class participation (Low)",
                evidence=f"Participation score: {score:.1f}",
                value=raw,
                extra={"score": score, "category": category},
            )
        return make_item("Class participation (Low)", evidence="Participation is Low", value=raw)

    if str(feature_name).startswith("Study_Habits_"):
        # Keep this out of the "low risk" view to avoid over coaching.
        if risk_label == "Low":
            return None

        category = str(feature_name).split("Study_Habits_", 1)[1].strip()
        raw = str(row.get("Study_Habits", "")).strip()

        # Only treat "Poor" study habits as a risk factor.
        risk_categories = {"Poor"}
        if raw != category or category not in risk_categories:
            return None

        return make_item(
            "Study habits",
            evidence="Poor study habits",
            value=raw,
            extra={"category": category},
        )

    return None


def predict_risk(df):
    X = df.drop(columns=[TARGET_COLUMN], errors="ignore")

    df["risk_prediction"] = model.predict(X)
    df["risk_probability"] = model.predict_proba(X)[:, 1]
    df["pass_probability"] = 1 - df["risk_probability"]
    df["risk_label"] = df["risk_probability"].apply(get_risk_label)

    preprocessor = model.named_steps["preprocessor"]
    rf_model = model.named_steps["model"]

    transformed_feature_names = list(preprocessor.get_feature_names_out())
    feature_importances = np.asarray(rf_model.feature_importances_, dtype=float)
    if feature_importances.sum() > 0:
        feature_importances = feature_importances / feature_importances.sum()

    valid_idx = []
    importance_map = {}
    for i, feature_name in enumerate(transformed_feature_names):
        cleaned = _clean_feature_name(feature_name)
        if cleaned.startswith(EXCLUDED_FEATURE_PREFIXES):
            continue
        if cleaned not in ALLOWED_RISK_FEATURES:
            continue
        if feature_importances[i] <= 0:
            continue
        valid_idx.append(i)
        importance_map[cleaned] = float(feature_importances[i])

    top_features_per_row = []
    recommendations_per_row = []

    risk_probs = df["risk_probability"].tolist()

    for row_idx, (_, row) in enumerate(X.iterrows()):
        risk_prob = float(risk_probs[row_idx])
        risk_label = get_risk_label(risk_prob)

        weighted_scores = []
        for i in valid_idx:
            cleaned_name = _clean_feature_name(transformed_feature_names[i])
            base_importance = importance_map.get(cleaned_name, 0.0)
            signal = _risk_signal(cleaned_name, row)
            contribution = signal * base_importance
            if contribution <= 0:
                continue
            weighted_scores.append((cleaned_name, contribution, base_importance))

        if not weighted_scores:
            top_features_per_row.append([])
            recommendations_per_row.append(generate_recommendations(risk_prob, []))
            continue

        weighted_scores.sort(key=lambda item: item[1], reverse=True)
        candidate_items = weighted_scores[:15]

        # Always check core academic drivers (exams, GPA, attendance, assignments),
        # even if the model importance ranking does not surface them for a student.
        must_check_features = [
            "GPA",
            "Midterm_Score",
            "Final_Score",
            "Attendance_Percentage",
            "Assignment_Completion_Percentage",
            "Quiz_Pass_Rate",
            "Avg_Quiz_Score",
        ]

        def _feature_type_for(name: str) -> str:
            if name in {"Attendance_Percentage", "Classes_Attended", "Classes_Missed"}:
                return "attendance"
            if str(name).startswith("Quiz_") and str(name).endswith("_Score"):
                return "quiz"
            if name in {"Avg_Quiz_Score", "Quiz_Pass_Rate"}:
                return "quiz_aggregate"
            if name == "Midterm_Score":
                return "midterm"
            if name == "Final_Score":
                return "final"
            if name in {"Assignment_Completion_Percentage", "Assignments_Completed"}:
                return "assignment_completion"
            if name == "GPA":
                return "gpa"
            if str(name).startswith("Class_Participation_"):
                return "class_participation"
            if str(name).startswith("Study_Habits_"):
                return "study_habits"
            return "other"

        confirmed_risk_factors = []
        seen_labels = set()

        # Optional: surface probation explicitly as a risk factor for clarity.
        academic_status = str(row.get("Academic_Status", "")).strip().lower()
        if "probation" in academic_status:
            confirmed_risk_factors.append(
                {
                    "feature": "Academic_Status",
                    "importance": 0.0,
                    "label": "Academic standing",
                    "evidence": "On probation",
                    "value": row.get("Academic_Status"),
                    "type": "academic_status",
                }
            )
            seen_labels.add("Academic standing")

        # First pass: confirm must check features using real thresholds.
        for feature_name in must_check_features:
            confirmed = _confirm_risk_factor(
                feature_name=feature_name,
                row=row,
                importance=importance_map.get(feature_name, 0.0),
                risk_label=risk_label,
            )
            if not confirmed:
                continue
            risk_label_text = confirmed.get("label")
            if risk_label_text and risk_label_text in seen_labels:
                continue
            confirmed_risk_factors.append({**confirmed, "type": _feature_type_for(feature_name)})
            if risk_label_text:
                seen_labels.add(risk_label_text)

        # Second pass: add additional confirmed factors from the model ranked list.
        for feature_name, _, base_importance in candidate_items:
            confirmed = _confirm_risk_factor(
                feature_name=feature_name,
                row=row,
                importance=base_importance,
                risk_label=risk_label,
            )
            if not confirmed:
                continue
            risk_label_text = confirmed.get("label")
            if risk_label_text and risk_label_text in seen_labels:
                continue

            confirmed_risk_factors.append({**confirmed, "type": _feature_type_for(feature_name)})
            if risk_label_text:
                seen_labels.add(risk_label_text)
            if len(confirmed_risk_factors) >= 10:
                break

        top_features_per_row.append(confirmed_risk_factors)
        recommendations_per_row.append(generate_recommendations(risk_prob, confirmed_risk_factors))

    df["top_features"] = top_features_per_row
    df["recommendations"] = recommendations_per_row

    return df


def predict_student_output(df):
    """
    Returns structured prediction output for a single student row.
    """
    scored_df = predict_risk(df.copy())
    row = scored_df.iloc[0]
    return {
        "risk_prob": float(row["risk_probability"]),
        "pass_prob": float(row["pass_probability"]),
        "label": row["risk_label"],
        "top_features": row["top_features"],
        "recommendations": row["recommendations"],
    }
