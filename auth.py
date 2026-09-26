# auth.py
import os
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

from utils.db_utils import get_student_by_id, get_students_by_filters


def _load_local_env_file(env_path=".env"):
    """Minimal .env loader to avoid extra dependencies."""
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env_file()

AUTH_DB_PATH = "student_portal.db"
# demo friendly defaults in .env, not in source code.
DEFAULT_DEMO_PASSWORD = os.environ.get("DEFAULT_DEMO_PASSWORD", "changeme")
STUDENT_PASSWORD = os.environ.get("STUDENT_DEFAULT_PASSWORD", DEFAULT_DEMO_PASSWORD)
TEACHER_PASSWORD = os.environ.get("TEACHER_DEFAULT_PASSWORD", DEFAULT_DEMO_PASSWORD)

MAJORS = {
    "Computer Science": "CS",
    "Business Administration": "BA",
    "Engineering": "EN",
    "Psychology": "PS",
    "Biology": "BI",
    "Economics": "EC",
    "English": "ENG",
    "Mathematics": "MATH",
    "Political Science": "POLS",
    "Chemistry": "CHEM",
    "History": "HIST",
    "Nursing": "NURS",
    "Physics": "PHYS",
    "Sociology": "SOC",
    "Art": "ART",
    "Communications": "COMM",
    "Education": "EDU",
    "Marketing": "MKT",
    "Finance": "FIN",
    "Data Science": "DS"
}

SEMESTER_CODES = {
    "Spring 2021": "SP21",
    "Fall 2021": "FA21",
    "Spring 2022": "SP22",
    "Fall 2022": "FA22",
    "Spring 2023": "SP23",
    "Fall 2023": "FA23",
    "Spring 2024": "SP24",
    "Fall 2024": "FA24"
}

# Generate teacher credentials for all majors
TEACHERS = {
    "teacher_art": {
        "password": os.environ.get("TEACHER_ART_PASSWORD", TEACHER_PASSWORD),
        "role": "teacher",
        "major": "Art"
    }
}

# Add all other teachers
for major_name, major_code in MAJORS.items():
    username = f"{major_code.lower()}teacher"
    TEACHERS[username] = {
        "password": TEACHER_PASSWORD,
        "role": "teacher",
        "major": major_name
    }


def get_sample_students_by_semester_major(semester_code, major_code, get_students_by_filters, limit=20):
    """Get sample student IDs from the database filtered by semester and major
    
    Uses the existing get_students_by_filters function from db_utils
    """
    try:
        print(f"Loading students for {semester_code}-{major_code}")
        
        # Get all students
        df = get_students_by_filters()
        
        if df.empty:
            print("No students found in database")
            return []
        
        # Filter by the pattern: semester_code-major_code-*
        pattern = f"{semester_code}-{major_code}-"
        filtered_df = df[df['Student_ID'].str.startswith(pattern)]
        
        print(f"Found {len(filtered_df)} students matching {pattern}")
        
        if filtered_df.empty:
            return []
        
        # Get random sample
        sample_size = min(limit, len(filtered_df))
        sample_df = filtered_df.sample(n=sample_size)
        
        student_ids = sample_df['Student_ID'].tolist()
        print(f"Returning {len(student_ids)} student IDs: {student_ids[:3]}...")
        
        return student_ids
        
    except Exception as e:
        print(f"Error loading students: {e}")
        import traceback
        traceback.print_exc()
        return []


def _get_auth_connection():
    return sqlite3.connect(AUTH_DB_PATH)


def _ensure_users_table():
    with _get_auth_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _upsert_user(username, raw_password, role):
    password_hash = generate_password_hash(raw_password)
    with _get_auth_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                role = excluded.role
            """,
            (username, password_hash, role),
        )
        conn.commit()


def _get_user(username, role=None):
    query = "SELECT id, username, password_hash, role FROM users WHERE username = ?"
    params = [username]
    if role:
        query += " AND role = ?"
        params.append(role)

    with _get_auth_connection() as conn:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "username": row[1],
            "password_hash": row[2],
            "role": row[3],
        }


def init_auth_db():
    """Create users table and seed default teacher accounts."""
    _ensure_users_table()
    for username, teacher_data in TEACHERS.items():
        _upsert_user(username, teacher_data["password"], teacher_data["role"])


def authenticate_teacher(username, password):
    user = _get_user(username, role="teacher")
    if not user or not check_password_hash(user["password_hash"], password or ""):
        return None

    teacher_meta = TEACHERS.get(username, {})
    return {
        "role": "teacher",
        "username": username,
        "major": teacher_meta.get("major"),
    }


def authenticate_student(student_id, password, get_student_by_id):
    """Authenticate student via users table, creating first-login account if missing."""
    df = get_student_by_id(student_id)
    if df.empty:
        return None

    user = _get_user(student_id, role="student")
    if not user:
        _upsert_user(student_id, STUDENT_PASSWORD, "student")
        user = _get_user(student_id, role="student")

    if not user or not check_password_hash(user["password_hash"], password or ""):
        return None

    return {"role": "student", "student_id": student_id}