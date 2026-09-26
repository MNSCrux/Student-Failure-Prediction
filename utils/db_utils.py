import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///student_portal.db")

def get_students_by_filters(major=None, semester=None):
    query = "SELECT * FROM students WHERE 1=1"

    if major:
        query += " AND Major = :major"
    if semester:
        query += " AND Program_Semester = :semester"

    return pd.read_sql(
        query,
        engine,
        params={"major": major, "semester": semester}
    )
def get_student_by_id(student_id):
    query = "SELECT * FROM students WHERE Student_ID = :student_id"
    return pd.read_sql(
        query,
        engine,
        params={"student_id": student_id}
    )