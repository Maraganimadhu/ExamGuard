import hashlib
from datetime import datetime
from database import get_db


def save_evidence(
    candidate_id,
    session_id,
    evidence_type,
    filename,
    mime_type,
    file_data,
    sha256_hash=None
):
    """
    Store examination evidence in the database.
    Calculates SHA-256 hash automatically if not provided.
    """
    if not sha256_hash:
        sha256_hash = hashlib.sha256(file_data).hexdigest()

    connection = get_db()

    try:
        created_at = datetime.now().isoformat()

        cursor = connection.execute("""
            INSERT INTO evidence
            (
                candidate_id,
                session_id,
                evidence_type,
                filename,
                mime_type,
                file_data,
                sha256_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            candidate_id,
            session_id,
            evidence_type,
            filename,
            mime_type,
            file_data,
            sha256_hash,
            created_at
        ))

        connection.commit()
        evidence_id = cursor.lastrowid

        print("================================")
        print("EVIDENCE SAVED")
        print("================================")
        print("ID           :", evidence_id)
        print("Candidate ID :", candidate_id)
        print("Session ID   :", session_id)
        print("Evidence     :", evidence_type)
        print("Filename     :", filename)
        print("MIME Type    :", mime_type)
        print("Hash         :", sha256_hash)
        print("Created At   :", created_at)
        print("================================")

        return {
            "success": True,
            "id": evidence_id,
            "sha256_hash": sha256_hash
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def verify_evidence(evidence_id):
    """
    Verify tamper-evident SHA-256 hash of stored evidence by recomputing it from the file bytes.
    """
    connection = get_db()
    try:
        row = connection.execute("""
            SELECT id, sha256_hash, file_data
            FROM evidence
            WHERE id = ?
        """, (evidence_id,)).fetchone()

        if not row:
            return {
                "success": False,
                "message": "Evidence is invalid",
                "reason": "Evidence not found"
            }

        file_bytes = row["file_data"]
        stored_hash = row["sha256_hash"]

        if not file_bytes:
            return {
                "success": False,
                "message": "Evidence is invalid",
                "reason": "Empty file data"
            }

        calculated_hash = hashlib.sha256(file_bytes).hexdigest()

        if calculated_hash == stored_hash:
            return {
                "success": True,
                "message": "Evidence is valid",
                "evidence_id": evidence_id,
                "stored_hash": stored_hash,
                "calculated_hash": calculated_hash
            }
        else:
            return {
                "success": False,
                "message": "Evidence is invalid",
                "evidence_id": evidence_id,
                "stored_hash": stored_hash,
                "calculated_hash": calculated_hash
            }
    finally:
        connection.close()


if __name__ == "__main__":
    test_data = b"TEST SCREENSHOT DATA"
    result = save_evidence(
        candidate_id=1,
        session_id="test-evidence-session",
        evidence_type="screenshot",
        filename="test_screenshot.jpg",
        mime_type="image/jpeg",
        file_data=test_data
    )
    print("Evidence result:", result)
    verify_res = verify_evidence(result["id"])
    print("Verification result:", verify_res)