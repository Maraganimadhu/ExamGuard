from datetime import datetime
from database import get_db


def create_incident(
    candidate_id,
    session_id,
    event_type,
    description,
    severity
):
    """
    Log an incident event in the incident_logs table.
    """
    connection = get_db()
    try:
        now = datetime.now().isoformat()
        connection.execute("""
            INSERT INTO incident_logs
            (candidate_id, session_id, event_type, description, severity, event_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            candidate_id,
            session_id,
            event_type,
            description,
            severity,
            now,
            now
        ))
        connection.commit()
        print("================================")
        print("INCIDENT LOG CREATED")
        print("Candidate ID :", candidate_id)
        print("Session ID   :", session_id)
        print("Event Type   :", event_type)
        print("Severity     :", severity)
        print("Description  :", description)
        print("================================")
        return True
    except Exception as e:
        print(f"Error creating incident log: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()
