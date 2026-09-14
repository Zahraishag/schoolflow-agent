from strands import Agent
from strands.models.ollama import OllamaModel

from decision_engine import (
    get_connection,
    get_affected_lessons,
    get_ranked_candidates,
)


def build_schoolflow_context(disruption_id: int) -> str:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            disruptions.disruption_id,
            disruptions.school_id,
            disruptions.teacher_id,
            disruptions.type,
            disruptions.day,
            disruptions.period,
            disruptions.reason,
            teachers.teacher_name
        FROM disruptions
        JOIN teachers
            ON disruptions.teacher_id = teachers.teacher_id
        WHERE disruptions.disruption_id = ?
        """,
        (disruption_id,),
    )

    disruption = cursor.fetchone()

    if not disruption:
        connection.close()
        return "No disruption found."

    lessons = get_affected_lessons(
        connection,
        disruption["teacher_id"],
        disruption["day"],
    )

    assigned_today = {}
    lesson_summaries = []

    for lesson in lessons:

        if (
            disruption["period"] is not None
            and lesson["period"] != disruption["period"]
        ):
            continue

        candidates = get_ranked_candidates(
            connection,
            disruption["school_id"],
            disruption["teacher_id"],
            lesson,
            assigned_today,
        )

        if candidates:
            best = candidates[0]

            assigned_today[best["teacher_id"]] = (
                assigned_today.get(best["teacher_id"], 0) + 1
            )

            lesson_summaries.append(
                f"""
Affected Lesson
Period: {lesson["period"]}
Class: {lesson["class_name"]}
Subject: {lesson["subject"]}

Decision Engine Recommendation
Teacher: {best["teacher_name"]}
Score: {best["score"]}
Reasons: {", ".join(best["reasons"])}
"""
            )

        else:
            lesson_summaries.append(
                f"""
Affected Lesson
Period: {lesson["period"]}
Class: {lesson["class_name"]}
Subject: {lesson["subject"]}

Decision Engine Recommendation
No eligible substitute found.
Escalation to the school supervisor is required.
"""
            )

    connection.close()

    return f"""
SCHOOLFLOW STRUCTURED DATA

Disruption Type: {disruption["type"]}
Absent Teacher: {disruption["teacher_name"]}
Day: {disruption["day"]}
Reason: {disruption["reason"]}

DECISION ENGINE RESULTS

{"".join(lesson_summaries)}
"""


def create_schoolflow_agent():

    model = OllamaModel(
        host="http://localhost:11434",
        model_id="llama3.2:1b",
        temperature=0.1,
    )

    system_prompt = """
You are SchoolFlow Agent.

SchoolFlow helps school supervisors manage timetable disruptions.

You receive VERIFIED structured results from the SchoolFlow
deterministic decision engine.

You must explain those results.

STRICT RULES:

1. Never invent teachers.
2. Never invent substitute recommendations.
3. Use only recommendations provided by the decision engine.
4. Respect all hard constraints.
5. If the decision engine says no eligible substitute exists,
   say that escalation is required.
6. You may recommend a substitute but you NEVER approve one.
7. You NEVER execute timetable changes.
8. EVERY timetable change requires human supervisor approval.
9. Human approval is ALWAYS required.
10. Never state that human approval is not required.

SchoolFlow follows a Human-in-the-Loop model.

Your role:
Decision Engine -> Explain Recommendation -> Human Approval -> Execution
"""

    return Agent(
        model=model,
        system_prompt=system_prompt,
    )


def analyze_disruption(disruption_id: int = 1):

    context = build_schoolflow_context(disruption_id)

    agent = create_schoolflow_agent()

    prompt = f"""
Analyze the following SchoolFlow case:

{context}

Explain:

1. Disruption Summary
2. Recommended Substitute
3. Why This Recommendation
4. Workload / Fairness Check

IMPORTANT:
Do NOT create a Human Approval section.
The application adds the mandatory human approval rule itself.
"""

    response = agent(prompt)

    # Convert the Strands response to text
    response_text = str(response)

    # Safety correction in case the small local model contradicts
    # the SchoolFlow human-approval policy.
    response_text = response_text.replace(
        "No human approval is required.",
        ""
    )

    response_text = response_text.replace(
        "Human approval is not required.",
        ""
    )

    final_response = f"""
{response_text}

------------------------------------------------------------
HUMAN APPROVAL REQUIRED
YES.

SchoolFlow never executes a timetable change automatically.
The school supervisor must review and approve the recommendation
before the timetable is updated.
------------------------------------------------------------
"""

    return final_response


if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("SCHOOLFLOW STRANDS AGENT")
    print("=" * 60)

    result = analyze_disruption(1)

    print(result)