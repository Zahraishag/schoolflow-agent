# SchoolFlow Agent

SchoolFlow is an AI-assisted system for managing school timetable disruptions.

It helps school administrators respond to teacher absences by identifying affected lessons, finding eligible substitutes, checking constraints, ranking candidates, explaining the recommendation, and keeping the final decision with the human supervisor.

## The Problem

When a teacher becomes unavailable, school administrators often need to manually:

- identify affected lessons
- find available substitute teachers
- check timetable conflicts
- verify specialization and school stage
- check workload
- distribute substitutions fairly
- update the timetable

This process can be slow and can create new conflicts.

## The Solution

SchoolFlow turns this into a structured workflow:

Disruption  
→ Affected Lessons  
→ Candidate Teachers  
→ Hard Constraints  
→ Candidate Scoring  
→ Recommendation  
→ Human Approval  
→ Timetable Update

## Current MVP

The working MVP currently supports teacher absence management.

A school administrator can:

1. Register a teacher absence.
2. Select the day or a specific lesson.
3. Let SchoolFlow identify affected lessons.
4. Let the system search for eligible substitutes.
5. Review the recommended substitute.
6. See why the teacher was selected.
7. Approve or reject each lesson independently.
8. Apply the approved substitution to the timetable.

## Decision Rules

Before a teacher can be considered as a substitute, SchoolFlow checks mandatory rules.

The substitute must:

- be active
- be present
- be free during the lesson
- have no timetable conflict
- match the required specialization
- match the required school stage
- stay within the maximum workload

If no eligible substitute exists, SchoolFlow escalates the case to the supervisor instead of forcing a recommendation.

## Candidate Scoring

Eligible teachers are ranked using explainable factors:

| Factor | Weight |
|---|---:|
| Same specialization | 30 |
| Same school stage | 25 |
| Workload | 20 |
| Fairness / previous substitutions | 10 |
| Same-day repeated assignment | Penalty |

This helps prevent repeatedly assigning the same teacher when alternatives exist.

## Explainable Decisions

SchoolFlow stores information about every proposed substitution, including:

- original teacher
- proposed substitute
- affected lesson
- score
- explanation
- approval status
- approving supervisor
- approval time

Example:

> Kholoud was selected because she is the only eligible candidate who meets the specialization, stage, workload, availability, and conflict requirements.

## Human-in-the-Loop

SchoolFlow keeps the school supervisor in control.

Agent proposes  
→ Human reviews  
→ Human approves or rejects  
→ System executes

The timetable is not changed automatically without human approval.

## Product Vision

SchoolFlow is being designed as a configurable product for schools.

Future school settings can include:

- school name
- school logo
- brand color
- school type
- boys / girls section
- school stages
- workload rules
- substitution rules
- approval policies
- scoring weights

This will allow the same SchoolFlow platform to serve multiple schools.

## Planned Extensions

The current MVP focuses on teacher absence.

Future versions can support:

- teacher reassignment
- teacher transfer to another class
- teacher transfer to another school
- teacher availability changes
- timetable conflicts
- room conflicts
- multiple simultaneous absences
- exam-day changes
- notifications
- timetable history
- analytics

## Architecture

School Supervisor  
↓  
Streamlit Dashboard  
↓  
Disruption Manager  
↓  
Decision Engine  
↓  
Hard Constraints + Scoring + Ranking  
↓  
Explainable Recommendation  
↓  
Human Approval  
↓  
Timetable Update  
↓  
SQLite Database

## Technology Stack

- Python
- SQLite
- Streamlit
- Git
- GitHub

Planned agent integration:

- Strands Agents SDK
- Ollama
- optional AWS services

## Project Structure

SchoolFlow/
- app.py
- database.py
- decision_engine.py
- schema.sql
- seed.sql
- check_data.py
- check_assignments.py
- apply_approved_assignments.py
- .gitignore
- README.md

## Run Locally

Create the database:

    python database.py

Install Streamlit:

    python -m pip install streamlit

Run SchoolFlow:

    python -m streamlit run app.py

Then open:

    http://localhost:8501

## Demo Scenario

1. Sara is absent on Monday.
2. SchoolFlow identifies her affected mathematics lessons.
3. The system searches for eligible substitutes.
4. Kholoud is proposed as the best eligible substitute.
5. SchoolFlow explains why she was selected.
6. The supervisor approves the substitution.
7. The assignment is stored.
8. The timetable is updated from Sara to Kholoud.

## Why SchoolFlow Matters

School timetable disruptions happen every day.

SchoolFlow helps administrators respond faster while reducing conflicts and keeping human oversight.

The goal is not to replace school administrators.

The goal is to help them make faster, safer, and more transparent decisions.

## Vision

> Something changed. Fix the timetable without breaking the school day.

The long-term goal is to build a school operations agent that understands timetable disruptions, evaluates their impact, proposes the safest solution, and keeps humans in control.

## Current Working Features

- teacher absence registration
- affected lesson detection
- candidate filtering
- timetable conflict checking
- workload checking
- candidate scoring
- fairness logic
- explainable recommendations
- per-lesson approval
- persistent assignment records
- timetable updates after approval
- Arabic RTL dashboard

## Author

Dr. Zahra Idris Al-Ansari

SchoolFlow / CoverWise