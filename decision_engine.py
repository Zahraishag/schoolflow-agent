import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "schoolflow.db"


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# LESSONS
# =========================================================

def get_affected_lessons(connection, teacher_id, day):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            timetable.timetable_id,
            timetable.day,
            timetable.period,
            timetable.subject,
            timetable.class_id,
            classes.class_name,
            classes.stage
        FROM timetable
        JOIN classes
            ON timetable.class_id = classes.class_id
        WHERE timetable.teacher_id = ?
          AND timetable.day = ?
        ORDER BY timetable.period
    """, (teacher_id, day))

    return cursor.fetchall()


# =========================================================
# CANDIDATES
# =========================================================

def get_candidate_teachers(
    connection,
    school_id,
    absent_teacher_id
):
    cursor = connection.cursor()

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
        WHERE school_id = ?
          AND teacher_id != ?
          AND is_present = 1
          AND is_active = 1
    """, (
        school_id,
        absent_teacher_id
    ))

    return cursor.fetchall()


# =========================================================
# CONFLICT CHECK
# =========================================================

def has_conflict(
    connection,
    teacher_id,
    day,
    period
):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM timetable
        WHERE teacher_id = ?
          AND day = ?
          AND period = ?
    """, (
        teacher_id,
        day,
        period
    ))

    return cursor.fetchone()[0] > 0


# =========================================================
# SCORING
# =========================================================

def score_candidate(
    candidate,
    lesson,
    assigned_today
):
    score = 0
    reasons = []

    # -----------------------------------------
    # Specialization
    # -----------------------------------------

    if candidate["specialization"] == lesson["subject"]:
        score += 30
        reasons.append(
            "Same specialization +30"
        )

    # -----------------------------------------
    # Stage
    # -----------------------------------------

    if candidate["stage"] == lesson["stage"]:
        score += 25
        reasons.append(
            "Same stage +25"
        )

    # -----------------------------------------
    # Workload
    # -----------------------------------------

    workload_ratio = (
        candidate["current_load"]
        / candidate["max_load"]
    )

    workload_score = round(
        20 * (1 - workload_ratio),
        2
    )

    score += workload_score

    reasons.append(
        f"Workload +{workload_score}"
    )

    # -----------------------------------------
    # Historical fairness
    # -----------------------------------------

    fairness_score = max(
        0,
        10
        - candidate["previous_substitutions"] * 2
    )

    score += fairness_score

    reasons.append(
        f"Fairness +{fairness_score}"
    )

    # -----------------------------------------
    # Today's assignments
    # -----------------------------------------

    assignments_today = assigned_today.get(
        candidate["teacher_id"],
        0
    )

    daily_penalty = (
        assignments_today * 10
    )

    if daily_penalty > 0:

        score -= daily_penalty

        reasons.append(
            f"Daily assignment penalty "
            f"-{daily_penalty}"
        )

    return (
        round(score, 2),
        reasons
    )


# =========================================================
# RANK CANDIDATES
# =========================================================

def get_ranked_candidates(
    connection,
    school_id,
    absent_teacher_id,
    lesson,
    assigned_today
):
    candidates = get_candidate_teachers(
        connection,
        school_id,
        absent_teacher_id
    )

    eligible_candidates = []

    for candidate in candidates:

        # -------------------------------------
        # HARD CONSTRAINT 1
        # No schedule conflict
        # -------------------------------------

        if has_conflict(
            connection,
            candidate["teacher_id"],
            lesson["day"],
            lesson["period"]
        ):
            continue

        # -------------------------------------
        # HARD CONSTRAINT 2
        # Workload limit
        # -------------------------------------

        if (
            candidate["current_load"] + 1
            > candidate["max_load"]
        ):
            continue

        # -------------------------------------
        # HARD CONSTRAINT 3
        # Same specialization
        # -------------------------------------

        if (
            candidate["specialization"]
            != lesson["subject"]
        ):
            continue

        # -------------------------------------
        # HARD CONSTRAINT 4
        # Same stage
        # -------------------------------------

        if (
            candidate["stage"]
            != lesson["stage"]
        ):
            continue

        score, reasons = score_candidate(
            candidate,
            lesson,
            assigned_today
        )

        eligible_candidates.append({
            "teacher_id":
                candidate["teacher_id"],

            "teacher_name":
                candidate["teacher_name"],

            "score":
                score,

            "reasons":
                reasons,

            "current_load":
                candidate["current_load"],

            "assigned_today":
                assigned_today.get(
                    candidate["teacher_id"],
                    0
                )
        })


    eligible_candidates.sort(
        key=lambda item: (
            item["score"],
            -item["assigned_today"],
            -item["current_load"]
        ),
        reverse=True
    )

    return eligible_candidates


# =========================================================
# EXPLANATION
# =========================================================

def build_decision_explanation(
    ranked_candidates,
    lesson
):
    if not ranked_candidates:

        return (
            "No eligible candidate met "
            "all hard constraints."
        )

    best = ranked_candidates[0]

    if len(ranked_candidates) == 1:

        return (
            f"{best['teacher_name']} was selected "
            f"because she is the only eligible "
            f"candidate who meets the specialization, "
            f"stage, workload, availability, "
            f"and conflict requirements."
        )

    second = ranked_candidates[1]

    difference = round(
        best["score"]
        - second["score"],
        2
    )

    return (
        f"{best['teacher_name']} was selected over "
        f"{second['teacher_name']} because she "
        f"received the highest score. "
        f"Score difference: {difference}."
    )


# =========================================================
# SAVE PROPOSAL
# =========================================================

def save_substitution_assignment(
    connection,
    school_id,
    disruption_id,
    timetable_id,
    original_teacher_id,
    proposed_teacher_id,
    score,
    explanation
):
    cursor = connection.cursor()

    # Prevent duplicate proposals
    cursor.execute("""
        SELECT assignment_id
        FROM substitution_assignments
        WHERE disruption_id = ?
          AND timetable_id = ?
    """, (
        disruption_id,
        timetable_id
    ))

    existing = cursor.fetchone()

    if existing:

        cursor.execute("""
            UPDATE substitution_assignments
            SET
                proposed_teacher_id = ?,
                score = ?,
                explanation = ?,
                status = 'proposed'
            WHERE assignment_id = ?
        """, (
            proposed_teacher_id,
            score,
            explanation,
            existing["assignment_id"]
        ))

    else:

        cursor.execute("""
            INSERT INTO substitution_assignments (
                school_id,
                disruption_id,
                timetable_id,
                original_teacher_id,
                proposed_teacher_id,
                score,
                explanation,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'proposed')
        """, (
            school_id,
            disruption_id,
            timetable_id,
            original_teacher_id,
            proposed_teacher_id,
            score,
            explanation
        ))

    connection.commit()


# =========================================================
# PROCESS ABSENCE
# =========================================================

def process_absence(
    disruption_id=1,
    save_results=True
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            disruption_id,
            school_id,
            teacher_id,
            day,
            period,
            reason
        FROM disruptions
        WHERE disruption_id = ?
          AND type = 'absence'
    """, (
        disruption_id,
    ))

    disruption = cursor.fetchone()

    if not disruption:

        print(
            "Absence disruption not found."
        )

        connection.close()

        return []


    cursor.execute("""
        SELECT teacher_name
        FROM teachers
        WHERE teacher_id = ?
    """, (
        disruption["teacher_id"],
    ))

    absent_teacher = cursor.fetchone()


    affected_lessons = get_affected_lessons(
        connection,
        disruption["teacher_id"],
        disruption["day"]
    )


    # If absence is for one period only
    if disruption["period"] is not None:

        affected_lessons = [
            lesson
            for lesson in affected_lessons
            if lesson["period"]
            == disruption["period"]
        ]


    assigned_today = {}

    results = []


    print("\n" + "=" * 60)

    print(
        "SCHOOLFLOW DECISION ENGINE"
    )

    print("=" * 60)

    print(
        f"\nAbsent teacher: "
        f"{absent_teacher['teacher_name']}"
    )

    print(
        f"Day: "
        f"{disruption['day']}"
    )

    print(
        f"Affected lessons: "
        f"{len(affected_lessons)}"
    )


    for lesson in affected_lessons:

        print("\n" + "-" * 60)

        print(
            f"Period {lesson['period']} | "
            f"{lesson['class_name']} | "
            f"{lesson['subject']}"
        )


        ranked_candidates = get_ranked_candidates(
            connection,
            disruption["school_id"],
            disruption["teacher_id"],
            lesson,
            assigned_today
        )


        if not ranked_candidates:

            explanation = (
                "No teacher met all "
                "mandatory requirements."
            )

            print(
                "Result: "
                "No eligible substitute found."
            )

            print(
                "Action: "
                "Escalate to supervisor."
            )


            results.append({
                "timetable_id":
                    lesson["timetable_id"],

                "period":
                    lesson["period"],

                "class_name":
                    lesson["class_name"],

                "subject":
                    lesson["subject"],

                "teacher_id":
                    None,

                "teacher_name":
                    None,

                "score":
                    None,

                "explanation":
                    explanation,

                "status":
                    "escalate"
            })

            continue


        best = ranked_candidates[0]


        assigned_today[
            best["teacher_id"]
        ] = (
            assigned_today.get(
                best["teacher_id"],
                0
            ) + 1
        )


        explanation = (
            build_decision_explanation(
                ranked_candidates,
                lesson
            )
        )


        if save_results:

            save_substitution_assignment(
                connection=connection,

                school_id=
                    disruption["school_id"],

                disruption_id=
                    disruption[
                        "disruption_id"
                    ],

                timetable_id=
                    lesson["timetable_id"],

                original_teacher_id=
                    disruption["teacher_id"],

                proposed_teacher_id=
                    best["teacher_id"],

                score=
                    best["score"],

                explanation=
                    explanation
            )


        print(
            f"Best substitute: "
            f"{best['teacher_name']}"
        )

        print(
            f"Score: "
            f"{best['score']}"
        )

        print(
            "Action: "
            "Waiting for human approval."
        )


        results.append({
            "timetable_id":
                lesson["timetable_id"],

            "period":
                lesson["period"],

            "class_name":
                lesson["class_name"],

            "subject":
                lesson["subject"],

            "teacher_id":
                best["teacher_id"],

            "teacher_name":
                best["teacher_name"],

            "score":
                best["score"],

            "explanation":
                explanation,

            "reasons":
                best["reasons"],

            "alternatives":
                ranked_candidates[1:4],

            "status":
                "proposed"
        })


    connection.close()

    return results


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    process_absence(
        disruption_id=1,
        save_results=True
    )