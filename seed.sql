-- =========================
-- SCHOOL
-- =========================
INSERT INTO schools (
    school_name,
    school_logo,
    primary_color,
    school_type,
    school_section,
    stages,
    status
)
VALUES (
    'مدرسة SchoolFlow التجريبية',
    NULL,
    '#2563EB',
    'أهلية',
    'بنات',
    'ابتدائي,متوسط',
    'active'
);

-- =========================
-- SCHOOL SETTINGS
-- =========================
INSERT INTO school_settings (
    school_id,
    allow_cross_stage,
    require_same_specialization,
    max_substitutions_per_day,
    human_approval_required,
    specialization_weight,
    stage_weight,
    workload_weight,
    free_period_weight,
    fairness_weight
)
VALUES (
    1,
    0,
    1,
    2,
    1,
    30,
    25,
    20,
    15,
    10
);

-- =========================
-- TEACHERS
-- =========================
INSERT INTO teachers (
    school_id,
    teacher_name,
    specialization,
    stage,
    current_load,
    max_load,
    is_present,
    is_active,
    previous_substitutions
)
VALUES
(1, 'سارة', 'رياضيات', 'ابتدائي', 16, 20, 1, 1, 2),
(1, 'خلود', 'رياضيات', 'ابتدائي', 14, 20, 1, 1, 1),
(1, 'نورة', 'علوم', 'ابتدائي', 17, 20, 1, 1, 3),
(1, 'منى', 'علوم', 'متوسط', 15, 20, 1, 1, 1),
(1, 'هدى', 'لغة عربية', 'ابتدائي', 18, 20, 1, 1, 4),
(1, 'أمل', 'لغة عربية', 'متوسط', 16, 20, 1, 1, 2),
(1, 'ريم', 'إنجليزي', 'ابتدائي', 15, 20, 1, 1, 1),
(1, 'مها', 'إنجليزي', 'متوسط', 14, 20, 1, 1, 0);

-- =========================
-- CLASSES
-- =========================
INSERT INTO classes (
    school_id,
    stage,
    grade,
    section,
    class_name
)
VALUES
(1, 'ابتدائي', 'الرابع', 'أ', 'الرابع أ'),
(1, 'ابتدائي', 'الخامس', 'أ', 'الخامس أ'),
(1, 'ابتدائي', 'السادس', 'أ', 'السادس أ'),
(1, 'متوسط', 'الأول', 'أ', 'الأول متوسط أ'),
(1, 'متوسط', 'الثاني', 'أ', 'الثاني متوسط أ'),
(1, 'متوسط', 'الثالث', 'أ', 'الثالث متوسط أ');

-- =========================
-- TIMETABLE
-- =========================
INSERT INTO timetable (
    school_id,
    day,
    period,
    class_id,
    subject,
    teacher_id,
    room,
    is_locked
)
VALUES
(1, 'الاثنين', 1, 1, 'رياضيات', 1, '101', 0),
(1, 'الاثنين', 2, 2, 'رياضيات', 1, '102', 0),
(1, 'الاثنين', 3, 3, 'رياضيات', 2, '103', 0),

(1, 'الاثنين', 2, 1, 'علوم', 3, '201', 0),
(1, 'الاثنين', 3, 2, 'علوم', 3, '202', 0),

(1, 'الاثنين', 1, 3, 'لغة عربية', 5, '103', 0),

(1, 'الاثنين', 1, 4, 'علوم', 4, '301', 0),
(1, 'الاثنين', 2, 5, 'لغة عربية', 6, '302', 0),
(1, 'الاثنين', 3, 6, 'إنجليزي', 8, '303', 0);

-- =========================
-- FIRST DISRUPTION
-- =========================
INSERT INTO disruptions (
    school_id,
    type,
    teacher_id,
    day,
    period,
    reason,
    status
)
VALUES (
    1,
    'absence',
    1,
    'الاثنين',
    NULL,
    'غياب المعلمة سارة يوم الاثنين',
    'new'
);

-- =========================
-- SUBSTITUTION ASSIGNMENTS
-- نتركه فارغًا في البداية
-- لأن المحرك سيولد التكليفات لاحقًا
-- =========================