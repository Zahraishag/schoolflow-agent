import streamlit as st

from decision_engine import (
    get_connection,
    process_absence,
)


# =========================================================
# DATABASE HELPERS
# =========================================================

def get_school():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            school_id,
            school_name,
            school_logo,
            primary_color,
            school_type,
            school_section,
            stages
        FROM schools
        LIMIT 1
    """)

    school = cursor.fetchone()
    connection.close()

    return school


def get_teachers(school_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            teacher_id,
            teacher_name,
            specialization,
            stage
        FROM teachers
        WHERE school_id = ?
          AND is_active = 1
        ORDER BY teacher_name
    """, (school_id,))

    teachers = cursor.fetchall()
    connection.close()

    return teachers


def create_disruption(
    school_id,
    disruption_type,
    teacher_id,
    day,
    period,
    reason
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO disruptions (
            school_id,
            type,
            teacher_id,
            day,
            period,
            reason,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'new')
    """, (
        school_id,
        disruption_type,
        teacher_id,
        day,
        period,
        reason
    ))

    disruption_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return disruption_id


def get_disruptions(school_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            disruptions.disruption_id,
            disruptions.type,
            disruptions.teacher_id,
            disruptions.day,
            disruptions.period,
            disruptions.reason,
            disruptions.status,
            teachers.teacher_name
        FROM disruptions
        LEFT JOIN teachers
            ON disruptions.teacher_id = teachers.teacher_id
        WHERE disruptions.school_id = ?
        ORDER BY disruptions.disruption_id DESC
    """, (school_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows


def get_disruption(disruption_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            disruptions.disruption_id,
            disruptions.school_id,
            disruptions.teacher_id,
            disruptions.type,
            disruptions.day,
            disruptions.period,
            disruptions.reason,
            disruptions.status,
            teachers.teacher_name
        FROM disruptions
        LEFT JOIN teachers
            ON disruptions.teacher_id = teachers.teacher_id
        WHERE disruptions.disruption_id = ?
    """, (disruption_id,))

    row = cursor.fetchone()
    connection.close()

    return row


def get_assignments(disruption_id):
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
            substitution_assignments.proposed_teacher_id,
            substitution_assignments.original_teacher_id,
            substitution_assignments.approved_by,
            substitution_assignments.approved_at,

            proposed_teacher.teacher_name
                AS proposed_teacher_name,

            original_teacher.teacher_name
                AS original_teacher_name,

            timetable.day,
            timetable.period,
            timetable.subject,

            classes.class_name

        FROM substitution_assignments

        LEFT JOIN teachers AS proposed_teacher
            ON substitution_assignments.proposed_teacher_id
            = proposed_teacher.teacher_id

        LEFT JOIN teachers AS original_teacher
            ON substitution_assignments.original_teacher_id
            = original_teacher.teacher_id

        JOIN timetable
            ON substitution_assignments.timetable_id
            = timetable.timetable_id

        JOIN classes
            ON timetable.class_id
            = classes.class_id

        WHERE substitution_assignments.disruption_id = ?

        ORDER BY timetable.period
    """, (disruption_id,))

    rows = cursor.fetchall()
    connection.close()

    return rows


# =========================================================
# APPROVE AND EXECUTE
# =========================================================

def approve_assignment(
    assignment_id,
    approved_by="المشرفة"
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                assignment_id,
                timetable_id,
                proposed_teacher_id,
                status
            FROM substitution_assignments
            WHERE assignment_id = ?
        """, (assignment_id,))

        assignment = cursor.fetchone()

        if not assignment:
            return False, "لم يتم العثور على التكليف."

        if assignment["status"] == "approved":
            return False, "هذا التكليف معتمد مسبقًا."

        if not assignment["proposed_teacher_id"]:
            return False, "لا يوجد معلم بديل مقترح."

        # -----------------------------------------
        # 1. Update actual timetable
        # -----------------------------------------

        cursor.execute("""
            UPDATE timetable
            SET teacher_id = ?
            WHERE timetable_id = ?
        """, (
            assignment["proposed_teacher_id"],
            assignment["timetable_id"]
        ))

        # -----------------------------------------
        # 2. Approve assignment
        # -----------------------------------------

        cursor.execute("""
            UPDATE substitution_assignments
            SET
                status = 'approved',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP
            WHERE assignment_id = ?
        """, (
            approved_by,
            assignment_id
        ))

        # -----------------------------------------
        # 3. Update fairness history
        # -----------------------------------------

        cursor.execute("""
            UPDATE teachers
            SET previous_substitutions =
                previous_substitutions + 1
            WHERE teacher_id = ?
        """, (
            assignment["proposed_teacher_id"],
        ))

        connection.commit()

        return (
            True,
            "تم اعتماد التكليف وتحديث الجدول بنجاح."
        )

    except Exception as error:

        connection.rollback()

        return (
            False,
            f"حدث خطأ أثناء التنفيذ: {error}"
        )

    finally:
        connection.close()


# =========================================================
# REJECT
# =========================================================

def reject_assignment(
    assignment_id,
    approved_by="المشرفة"
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE substitution_assignments
        SET
            status = 'rejected',
            approved_by = ?,
            approved_at = CURRENT_TIMESTAMP
        WHERE assignment_id = ?
          AND status = 'proposed'
    """, (
        approved_by,
        assignment_id
    ))

    connection.commit()
    connection.close()


# =========================================================
# TRANSLATIONS
# =========================================================

def assignment_status_ar(status):
    values = {
        "proposed": "مقترح",
        "approved": "معتمد",
        "rejected": "مرفوض",
        "escalated": "مصعّد"
    }

    return values.get(status, status)


def disruption_status_ar(status):
    values = {
        "new": "جديدة",
        "approved": "معتمدة",
        "rejected": "مرفوضة",
        "pending": "قيد المراجعة"
    }

    return values.get(status, status)


def type_ar(disruption_type):
    values = {
        "absence": "غياب معلم",
        "reassignment": "نقل / إعادة إسناد معلم",
        "availability_change": "تغيّر توفر المعلم",
        "conflict": "تعارض في الجدول"
    }

    return values.get(
        disruption_type,
        disruption_type
    )


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="SchoolFlow",
    page_icon="🏫",
    layout="wide"
)


# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
<style>

html, body {
    direction: rtl;
}

.stApp {
    direction: rtl;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.school-header {
    background: linear-gradient(
        135deg,
        #111827,
        #172033
    );
    border: 1px solid #263244;
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 30px;
}

.brand-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.brand-title {
    font-size: 36px;
    font-weight: 800;
}

.school-name {
    font-size: 24px;
    font-weight: 700;
    margin-top: 16px;
}

.school-meta {
    margin-top: 8px;
    font-size: 15px;
    opacity: .75;
}

.section-title {
    font-size: 27px;
    font-weight: 800;
    margin-top: 30px;
    margin-bottom: 20px;
}

.lesson-title {
    font-size: 21px;
    font-weight: 800;
    margin-top: 25px;
    margin-bottom: 12px;
}

.explanation-box {
    background: #172033;
    border: 1px solid #2b3749;
    border-radius: 14px;
    padding: 18px;
    margin: 15px 0;
    line-height: 1.9;
}

div[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid #263244;
    padding: 18px;
    border-radius: 14px;
}

div[data-testid="stButton"] button {
    width: 100%;
    min-height: 48px;
    border-radius: 12px;
    font-weight: 700;
}

[data-testid="stAlert"] {
    border-radius: 14px;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# SCHOOL
# =========================================================

school = get_school()

if not school:
    st.error(
        "لم يتم العثور على بيانات المدرسة."
    )
    st.stop()


st.markdown(
    f"""<div class="school-header">
<div class="brand-row">
<div class="brand-title">🏫 SchoolFlow</div>
<div>نظام إدارة اضطرابات الجدول المدرسي</div>
</div>
<div class="school-name">{school["school_name"]}</div>
<div class="school-meta">
{school["school_type"]} |
{school["school_section"]} |
{school["stages"]}
</div>
</div>""",
    unsafe_allow_html=True
)


# =========================================================
# NEW DISRUPTION
# =========================================================

st.markdown(
    '<div class="section-title">إدارة التغييرات</div>',
    unsafe_allow_html=True
)


with st.expander(
    "➕ إضافة تغيير جديد"
):

    teachers = get_teachers(
        school["school_id"]
    )

    teacher_map = {
        teacher["teacher_name"]:
        teacher["teacher_id"]
        for teacher in teachers
    }

    type_map = {
        "غياب معلم":
            "absence",

        "نقل / إعادة إسناد معلم":
            "reassignment",

        "تغيّر توفر المعلم":
            "availability_change",

        "تعارض في الجدول":
            "conflict"
    }

    days = [
        "الأحد",
        "الاثنين",
        "الثلاثاء",
        "الأربعاء",
        "الخميس"
    ]

    with st.form(
        "new_disruption_form"
    ):

        c1, c2 = st.columns(2)

        with c1:

            selected_type = st.selectbox(
                "نوع التغيير",
                list(type_map.keys())
            )

            selected_teacher = st.selectbox(
                "المعلم / المعلمة",
                list(teacher_map.keys())
            )

        with c2:

            selected_day = st.selectbox(
                "اليوم",
                days
            )

            selected_period = st.selectbox(
                "الحصة",
                [
                    "اليوم كامل",
                    1, 2, 3, 4, 5, 6, 7
                ]
            )

        reason = st.text_area(
            "سبب التغيير",
            placeholder="مثال: إجازة مرضية"
        )

        submitted = (
            st.form_submit_button(
                "حفظ الحالة"
            )
        )

        if submitted:

            period_value = (
                None
                if selected_period
                == "اليوم كامل"
                else selected_period
            )

            new_id = create_disruption(
                school["school_id"],
                type_map[selected_type],
                teacher_map[selected_teacher],
                selected_day,
                period_value,
                reason
            )

            st.session_state[
                "selected_disruption_id"
            ] = new_id

            st.success(
                "تم تسجيل التغيير بنجاح."
            )

            st.rerun()


# =========================================================
# SELECT CASE
# =========================================================

disruptions = get_disruptions(
    school["school_id"]
)

if not disruptions:

    st.info(
        "لا توجد تغييرات مسجلة حتى الآن."
    )

    st.stop()


labels_map = {}

for item in disruptions:

    label = (
        f"#{item['disruption_id']} — "
        f"{type_ar(item['type'])} — "
        f"{item['teacher_name']} — "
        f"{item['day']}"
    )

    labels_map[label] = (
        item["disruption_id"]
    )


labels = list(labels_map.keys())

default_id = st.session_state.get(
    "selected_disruption_id",
    disruptions[0]["disruption_id"]
)

default_index = 0

for index, label in enumerate(labels):

    if labels_map[label] == default_id:
        default_index = index
        break


selected_label = st.selectbox(
    "الحالة التي تريدين مراجعتها",
    labels,
    index=default_index
)

selected_id = labels_map[
    selected_label
]

st.session_state[
    "selected_disruption_id"
] = selected_id


disruption = get_disruption(
    selected_id
)


# =========================================================
# CASE DETAILS
# =========================================================

st.markdown(
    '<div class="section-title">تفاصيل الحالة</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "نوع التغيير",
        type_ar(disruption["type"])
    )

with c2:
    st.metric(
        "المعلمة المتأثرة",
        disruption["teacher_name"]
    )

with c3:
    st.metric(
        "اليوم",
        disruption["day"]
    )

with c4:
    st.metric(
        "الحالة",
        disruption_status_ar(
            disruption["status"]
        )
    )


if disruption["reason"]:

    st.info(
        f"سبب التغيير: "
        f"{disruption['reason']}"
    )


# =========================================================
# ONLY ABSENCE WORKFLOW FOR NOW
# =========================================================

if disruption["type"] != "absence":

    st.warning(
        "تم تسجيل هذه الحالة، "
        "لكن محرك القرار الخاص بهذا النوع "
        "سيتم بناؤه لاحقًا."
    )

    st.stop()


# =========================================================
# GENERATE ASSIGNMENTS
# =========================================================

assignments = get_assignments(
    disruption["disruption_id"]
)

if not assignments:

    with st.spinner(
        "جارٍ تحليل الحالة وإنشاء الاقتراحات..."
    ):

        process_absence(
            disruption_id=
                disruption["disruption_id"],

            save_results=True
        )

    assignments = get_assignments(
        disruption["disruption_id"]
    )


# =========================================================
# ASSIGNMENTS
# =========================================================

st.markdown(
    '<div class="section-title">التكليفات المقترحة</div>',
    unsafe_allow_html=True
)


if not assignments:

    st.warning(
        "لم يتم إنشاء أي تكليفات لهذه الحالة."
    )

    st.stop()


for assignment in assignments:

    st.markdown(
        f"""<div class="lesson-title">
الحصة {assignment["period"]}
— {assignment["class_name"]}
— {assignment["subject"]}
</div>""",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [2, 1, 1]
    )

    with col1:

        st.success(
            f"البديلة المقترحة: "
            f"{assignment['proposed_teacher_name']}"
        )

    with col2:

        st.metric(
            "درجة الملاءمة",
            assignment["score"]
        )

    with col3:

        st.metric(
            "حالة التكليف",
            assignment_status_ar(
                assignment["status"]
            )
        )


    st.write(
        f"المعلمة الأصلية: "
        f"{assignment['original_teacher_name']}"
    )


    if assignment["explanation"]:

        st.markdown(
            f"""<div class="explanation-box">
<strong>تفسير القرار</strong><br><br>
{assignment["explanation"]}
</div>""",
            unsafe_allow_html=True
        )


    # =====================================================
    # APPROVE / REJECT
    # =====================================================

    if assignment["status"] == "proposed":

        approve_col, reject_col = (
            st.columns(2)
        )

        with approve_col:

            if st.button(
                "✅ اعتماد وتنفيذ",
                key=(
                    "approve_"
                    f"{assignment['assignment_id']}"
                )
            ):

                success, message = (
                    approve_assignment(
                        assignment[
                            "assignment_id"
                        ]
                    )
                )

                if success:

                    st.success(message)

                    st.rerun()

                else:

                    st.error(message)


        with reject_col:

            if st.button(
                "❌ رفض التكليف",
                key=(
                    "reject_"
                    f"{assignment['assignment_id']}"
                )
            ):

                reject_assignment(
                    assignment[
                        "assignment_id"
                    ]
                )

                st.warning(
                    "تم رفض التكليف."
                )

                st.rerun()


    elif assignment["status"] == "approved":

        st.success(
            "✅ تم اعتماد التكليف "
            "وتحديث الجدول فعليًا."
        )

        if assignment["approved_by"]:

            st.caption(
                f"اعتمد بواسطة: "
                f"{assignment['approved_by']}"
            )


    elif assignment["status"] == "rejected":

        st.warning(
            "❌ تم رفض هذا التكليف."
        )