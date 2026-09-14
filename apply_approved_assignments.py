from decision_engine import get_connection


def apply_approved_assignments():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            assignment_id,
            timetable_id,
            proposed_teacher_id
        FROM substitution_assignments
        WHERE status = 'approved'
          AND proposed_teacher_id IS NOT NULL
    """)

    assignments = cursor.fetchall()

    if not assignments:
        print("No approved assignments found.")
        connection.close()
        return

    for assignment in assignments:

        cursor.execute("""
            UPDATE timetable
            SET teacher_id = ?
            WHERE timetable_id = ?
        """, (
            assignment["proposed_teacher_id"],
            assignment["timetable_id"]
        ))

        print(
            f"Assignment {assignment['assignment_id']} applied."
        )

    connection.commit()
    connection.close()

    print("\nApproved assignments applied successfully.")


if __name__ == "__main__":
    apply_approved_assignments()
    