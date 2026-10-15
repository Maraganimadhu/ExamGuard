from database import get_db
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatPromptTemplate = None
    ChatOpenAI = None
    LANGCHAIN_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_session_data(candidate_id, session_id):
    connection = get_db()
    
    try:
        score = connection.execute("""
                                   SELECT integrity_score, risk_level, event_penalty, face_presence_ratio,computed_at
                                   FROM integrity_scores
                                   WHERE candidate_id = ?
                                   AND session_id = ?
                                   """, (
            candidate_id,
            session_id
        )).fetchone()
        if score is None:
            raise ValueError(
                f"No integrity score found for "
                f"candidate_id={candidate_id}, "
                f"session_id={session_id}"
            )
    
        events = connection.execute("""
                                    SELECT event_type, event_time, details from browser_events
                                    WHERE candidate_id = ?  and session_id = ?
                                    """, (candidate_id, session_id)).fetchall()
        
        face_events = connection.execute("""
                                    SELECT started_at, ended_at, duration_seconds
                                    FROM face_events
                                    WHERE candidate_id = ?  and session_id = ?
                                    """, (candidate_id, session_id)).fetchall() 
        
        return {
            "score": score,
            "browser_events": [dict(event) for event in events],
            "face_events": [dict(event) for event in face_events]
        }

    finally:
        connection.close()
        
def prepare_report_context(session_data):
    score = session_data["score"]
    browser_events = session_data["browser_events"]
    face_events = session_data["face_events"]

    report_context = {
        "integrity_score": score["integrity_score"],
        "risk_level": score["risk_level"],
        "event_penalty": score["event_penalty"],
        "face_presence_ratio": score["face_presence_ratio"],
        "computed_at": score["computed_at"],
        "browser_events": browser_events,
        "face_events": face_events
    }

    return report_context


def create_report_prompt():
    prompt = ChatPromptTemplate.from_template("""
You are an examination integrity reporting assistant.

Your job is to analyze the provided examination
session data and generate an evidence-based report.

SESSION INFORMATION

Integrity Score:
{integrity_score}

Risk Level:
{risk_level}

Event Penalty:
{event_penalty}

Face Presence Ratio:
{face_presence_ratio}%

Report Computed At:
{computed_at}


BROWSER EVENTS

{browser_events}


FACE MONITORING EVENTS

{face_events}


REPORT REQUIREMENTS

1. Explain the integrity score.

2. Explain the risk level.

3. Summarize the face monitoring information.

4. Summarize the browser activity.

5. Mention important observed events.

6. Use only the information provided.

7. Do not invent events or values.

8. Do not change or recalculate the integrity score.

9. Do not claim that an event proves misconduct.

10. Treat the result as a review-support report.

Write the report in a clear and professional format.
""")
    return prompt


def test_prompt():
    context = {
        "integrity_score": 85,
        "risk_level": "low",
        "event_penalty": 15,
        "face_presence_ratio": 98,
        "computed_at": "2024-06-01 12:00:00",
        "browser_events": [
            {"event_type": "tab_switch", "event_time": "2024-06-01 12:05:00", "details": None},
            {"event_type": "focus_loss", "event_time": "2024-06-01 12:10:00", "details": None}
        ],
        "face_events": [
            {"started_at": "2024-06-01 12:00:00", "ended_at": "2024-06-01 12:30:00", "duration_seconds": 1800}
        ]
    }
    prompt = create_report_prompt()
    messages = prompt.format_messages(**context)
    for message in messages:
        print(message.content)


def create_llm():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    return llm


def test_llm():
    llm = create_llm()
    response = llm.invoke(
        "You are an examination integrity reporting assistant."
    )
    print("LLM Response:", response)


def create_integrity_report():
    prompt = create_report_prompt()
    llm = create_llm()
    chain = prompt | llm
    return chain


def generate_real_integrity_report(candidate_id, session_id):
    session_data = get_session_data(candidate_id, session_id)
    report_context = prepare_report_context(session_data)

    if not LANGCHAIN_AVAILABLE:
        return (
            f"EXAMGUARD INTEGRITY SUMMARY REPORT\n"
            f"----------------------------------\n"
            f"Candidate ID: {candidate_id}\n"
            f"Session ID: {session_id}\n"
            f"Computed At: {report_context['computed_at']}\n\n"
            f"ASSESSMENT METRICS:\n"
            f"- Official Integrity Score: {report_context['integrity_score']} / 100\n"
            f"- Risk Level: {report_context['risk_level']}\n"
            f"- Face Presence Ratio: {report_context['face_presence_ratio']}%\n"
            f"- Event Deduction Penalty: -{report_context['event_penalty']}\n\n"
            f"SESSION OBSERVATIONS:\n"
            f"- Total Browser Events: {len(report_context['browser_events'])}\n"
            f"- Total Face Monitoring Intervals: {len(report_context['face_events'])}\n\n"
            f"AUDIT NOTE:\n"
            f"The candidate received an integrity score of {report_context['integrity_score']} "
            f"categorized under {report_context['risk_level']} risk. "
            f"This preliminary evidence summary was compiled from session telemetry."
        )

    chain = create_integrity_report()
    response = chain.invoke(report_context)
    report = response.content
    validation = validate_ai_report(report, report_context)
    if not validation["valid"]:
        raise ValueError(
            f"ai report validation failed {validation['reason']}"
        )
    return report


def validate_ai_report(report, report_context):
    if not report:
        return {
            "valid": False,
            "reason": "AI Report is empty"
        }
    integrity_score = str(report_context["integrity_score"])
    risk_level = str(report_context["risk_level"])
    if integrity_score not in report:
        return {
            "valid": False,
            "reason": "Integrity score missing from ai report"
        }
    if risk_level not in report:
        return {
            "valid": False,
            "reason": "Risk level missing from ai report"
        }
    forbidden_pharases = [
        "proved cheated",
        "proved misconduct",
        "definetly cheated",
        "candidate cheated"
    ]
    report_lower = report.lower()
    for pharases in forbidden_pharases:
        if pharases in report_lower:
            return {
                "valid": False,
                "reason": f"unsafe pharases found : {pharases}"
            }
    return {
        "valid": True,
        "Reason": "Ai report validation done"
    }