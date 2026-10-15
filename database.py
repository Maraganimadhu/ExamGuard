import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database", "examguard.db")


# ----------------------------------------
# DATABASE CONNECTION
# ----------------------------------------
def get_db():

    connection = sqlite3.connect(DATABASE)

    # Allows dictionary-style access:
    # candidate["id"]
    # candidate["name"]
    # candidate["email"]
    # candidate["password"]
    # candidate["photo"]
    # candidate["created_at"]

    connection.row_factory = sqlite3.Row
    return connection


# ----------------------------------------
# INITIALIZE DATABASE
# ----------------------------------------
def init_db():

    # Create database folder if it does not exist
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

    connection = get_db()


    # ----------------------------------------
    # CANDIDATES TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS candidates (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            password TEXT NOT NULL,

            photo TEXT,

            created_at TEXT
        )
    """)


    # ----------------------------------------
    # CHECK CREATED_AT COLUMN
    # ----------------------------------------
    # This protects an older existing database.
    # If created_at already exists, nothing happens.
    # If it does not exist, the column is added.

    columns = connection.execute(
        "PRAGMA table_info(candidates)"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

    if "created_at" not in column_names:

        connection.execute(
            "ALTER TABLE candidates ADD COLUMN created_at TEXT"
        )


    # ----------------------------------------
    # FACE MONITORING EVENTS
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS face_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            candidate_id INTEGER NOT NULL,

            session_id TEXT NOT NULL,

            event_type TEXT NOT NULL,

            started_at TEXT NOT NULL,

            ended_at TEXT,

            duration_seconds REAL,

            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
        )
    """)


    # ----------------------------------------
    # BROWSER ACTIVITY EVENTS
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS browser_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            candidate_id INTEGER NOT NULL,

            session_id TEXT NOT NULL,

            event_type TEXT NOT NULL,

            event_time TEXT NOT NULL,

            details TEXT,

            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
        )
    """)


    # ----------------------------------------
    # SUSPICIOUS EVENTS
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS suspicious_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            candidate_id INTEGER NOT NULL,

            session_id TEXT NOT NULL,

            event_type TEXT NOT NULL,

            reason TEXT NOT NULL,

            event_time TEXT NOT NULL,

            severity TEXT NOT NULL,

            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
        )
    """)

    # ----------------------------------------
    # EXAM ANSWERS TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS exam_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option TEXT,
            is_correct INTEGER,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
        )
    """)


    # ----------------------------------------
    # EXAM SESSIONS TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            session_id TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            submitted_at TEXT,
            status TEXT DEFAULT 'in_progress',
            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
        )
    """)

    session_columns = [
        col["name"]
        for col in connection.execute("PRAGMA table_info(exam_sessions)").fetchall()
    ]
    if "session_id" not in session_columns:
        connection.execute("ALTER TABLE exam_sessions ADD COLUMN session_id TEXT")
    if "submitted_at" not in session_columns:
        connection.execute("ALTER TABLE exam_sessions ADD COLUMN submitted_at TEXT")


    # ----------------------------------------
    # INTEGRITY SCORES TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS integrity_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            candidate_id INTEGER NOT NULL,
            event_penalty REAL NOT NULL,
            face_presence_ratio REAL NOT NULL,
            integrity_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            computed_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)

    # ----------------------------------------
    # INCIDENT LOGS TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS incident_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            event_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)

    # ----------------------------------------
    # ALERTS TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)

    # ----------------------------------------
    # EVIDENCE TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            filename TEXT,
            mime_type TEXT,
            file_data BLOB,
            sha256_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)

    # ----------------------------------------
    # AI REPORTS TABLE
    # ----------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            report TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)

    # Save database changes
    connection.commit()
    connection.close()