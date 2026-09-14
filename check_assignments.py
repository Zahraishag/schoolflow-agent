from decision_engine import get_connection


def check_assignments():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            substitution_assignments.assignment_id,
            substitution_assignments.disruption_id,
            substitution_assignments.timetable_id,
            substitution_assignments.status,
            substitution_assignments.score,
            substitution_assignments.explanation,

            original_teacher.teacher_name AS original_teacher_name,
            proposed_teacher.teacher_name AS proposed_teacher_name,

            timetable.day,
            timetable.period,
            timetable.subject,
            classes.class_name

        FROM substitution_assignments

        JOIN teachers AS original_teacher
            ON substitution_assignments.original_teacher_id
            = original_teacher.teacher_id

        LEFT JOIN teachers AS proposed_teacher
            ON substitution_assignments.proposed_teacher_id
            = proposed_teacher.teacher_id

        JOIN timetable
            ON substitution_assignments.timetable_id
            = timetable.timetable_id

        JOIN classes
            ON timetable.class_id
            = classes.class_id

        ORDER BY substitution_assignments.assignment_id
    """)

    assignments = cursor.fetchall()

    print("\n" + "=" * 70)
    print("SUBSTITUTION ASSIGNMENTS")
    print("=" * 70)

    if not assignments:
        print("No assignments found.")

    for item in assignments:
        print("\n" + "-" * 70)

        print(
            f"Assignment ID: {item['assignment_id']}"
        )

        print(
            f"Disruption ID: {item['disruption_id']}"
        )

        print(
            f"Day: {item['day']}"
        )

        print(
            f"Period: {item['period']}"
        )

        print(
            f"Class: {item['class_name']}"
        )

        print(
            f"Subject: {item['subject']}"
        )

        print(
            f"Original teacher: "
            f"{item['original_teacher_name']}"
        )

        print(
            f"Proposed substitute: "
            f"{item['proposed_teacher_name']}"
        )

        print(
            f"Score: {item['score']}"
        )

        print(
            f"Status: {item['status']}"
        )

        print(
            f"Explanation: "
            f"{item['explanation']}"
        )

    connection.close()


if __name__ == "__main__":
    check_assignments()