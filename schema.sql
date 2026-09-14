PRAGMA foreign_keys = ON;

CREATE TABLE schools (
    school_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_name TEXT NOT NULL,
    school_logo TEXT,
    primary_color TEXT,
    school_type TEXT,
    school_section TEXT,
    stages TEXT,
    status TEXT DEFAULT 'active'
);

CREATE TABLE school_settings (
    settings_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,

    allow_cross_stage INTEGER DEFAULT 0,
    require_same_specialization INTEGER DEFAULT 1,
    max_substitutions_per_day INTEGER DEFAULT 2,
    human_approval_required INTEGER DEFAULT 1,

    specialization_weight INTEGER DEFAULT 30,
    stage_weight INTEGER DEFAULT 25,
    workload_weight INTEGER DEFAULT 20,
    free_period_weight INTEGER DEFAULT 15,
    fairness_weight INTEGER DEFAULT 10,

    FOREIGN KEY (school_id)
        REFERENCES schools(school_id)
        ON DELETE CASCADE
);

CREATE TABLE teachers (
    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,

    teacher_name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    stage TEXT,

    current_load INTEGER DEFAULT 0,
    max_load INTEGER DEFAULT 20,

    is_present INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,

    previous_substitutions INTEGER DEFAULT 0,

    FOREIGN KEY (school_id)
        REFERENCES schools(school_id)
        ON DELETE CASCADE
);

CREATE TABLE classes (
    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,

    stage TEXT NOT NULL,
    grade TEXT NOT NULL,
    section TEXT,
    class_name TEXT NOT NULL,

    FOREIGN KEY (school_id)
        REFERENCES schools(school_id)
        ON DELETE CASCADE
);

CREATE TABLE timetable (
    timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,

    day TEXT NOT NULL,
    period INTEGER NOT NULL,

    class_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    teacher_id INTEGER NOT NULL,

    room TEXT,
    is_locked INTEGER DEFAULT 0,

    FOREIGN KEY (school_id)
        REFERENCES schools(school_id)
        ON DELETE CASCADE,

    FOREIGN KEY (class_id)
        REFERENCES classes(class_id)
        ON DELETE CASCADE,

    FOREIGN KEY (teacher_id)
        REFERENCES teachers(teacher_id)
);

CREATE TABLE disruptions (
    disruption_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,

    type TEXT NOT NULL,
    teacher_id INTEGER,

    day TEXT NOT NULL,
    period INTEGER,

    reason TEXT,

    status TEXT DEFAULT 'new',

    approved_by TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (school_id)
        REFERENCES schools(school_id)
        ON DELETE CASCADE,

    FOREIGN KEY (teacher_id)
        REFERENCES teachers(teacher_id)
);

CREATE TABLE substitution_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    school_id INTEGER NOT NULL,
    disruption_id INTEGER NOT NULL,
    timetable_id INTEGER NOT NULL,

    original_teacher_id INTEGER NOT NULL,
    proposed_teacher_id INTEGER,

    score REAL,
    explanation TEXT,

    status TEXT DEFAULT 'proposed',

    approved_by TEXT,
    approved_at TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (school_id)
        REFERENCES schools(school_id)
        ON DELETE CASCADE,

    FOREIGN KEY (disruption_id)
        REFERENCES disruptions(disruption_id)
        ON DELETE CASCADE,

    FOREIGN KEY (timetable_id)
        REFERENCES timetable(timetable_id)
        ON DELETE CASCADE,

    FOREIGN KEY (original_teacher_id)
        REFERENCES teachers(teacher_id),

    FOREIGN KEY (proposed_teacher_id)
        REFERENCES teachers(teacher_id)
);