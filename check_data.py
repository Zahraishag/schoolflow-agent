import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "schoolflow.db"


def print_rows(title, rows):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    for row in rows:
        print(row)


def check_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # 1) المدرسة
    cursor.execute("""
        SELECT school_id, school_name, school_type, school_section, stages
        FROM schools
    """)
    print_rows("SCHOOLS", cursor.fetchall())

    # 2) المعلمون
    cursor.execute("""
        SELECT
            teacher_id,
            teacher_name,
            specialization,
            stage,
            current_load,
            max_load,
            is_present,
            is_active,
            previous_substitutions
        FROM teachers
        ORDER BY teacher_id
    """)
    print_rows("TEACHERS", cursor.fetchall())

    # 3) الجدول
    cursor.execute("""
        SELECT
            timetable.timetable_id,
            timetable.day,
            timetable.period,
            classes.class_name,
            timetable.subject,
            teachers.teacher_name
        FROM timetable
        JOIN classes
            ON timetable.class_id = classes.class_id
        JOIN teachers
            ON timetable.teacher_id = teachers.teacher_id
        ORDER BY timetable.day, timetable.period, classes.class_name
    """)
    print_rows("TIMETABLE", cursor.fetchall())

    # 4) الاضطرابات / التغييرات
    cursor.execute("""
        SELECT
            disruptions.disruption_id,
            disruptions.type,
            teachers.teacher_name,
            disruptions.day,
            disruptions.period,
            disruptions.reason,
            disruptions.status
        FROM disruptions
        LEFT JOIN teachers
            ON disruptions.teacher_id = teachers.teacher_id
        ORDER BY disruptions.disruption_id
    """)
    print_rows("DISRUPTIONS", cursor.fetchall())

    connection.close()


if __name__ == "__main__":
    check_database()