from monitoring.integrity_score import (get_risk_level, calculate_integrity_score, calculate_face_presence_ratio,calculate_event_penalty)

def _events(**counts):
    return [{"event_type": n} for n, k in counts.items() for _ in range(k)]

SCENARIOS = [
    ("low",    _events(tab_switch=1, focus_lost=1, mouse_activity=40), 98, "Low"),
    ("medium", _events(tab_switch=2, focus_lost=2, right_click=1),     98, "Medium"),
    ("high",   _events(tab_switch=5, focus_lost=3, copy_attempt=1,
                       paste_attempt=1, right_click=2),                45, "High"),
]

def main():
    for name, events, face, expected in SCENARIOS:
        score = calculate_integrity_score(events, face)
        risk = get_risk_level(score)
        print(f"{name}: score={score} risk={risk} expected={expected}")
        assert risk == expected, f"{name} scenario failed"
    print("All scoring scenarios passed.")
    
if __name__ == "__main__":
    main()

# LangChain is a framework for developing applications powered by language models. It provides a standard interface for interacting with language models, as well as a set of tools and utilities for building applications that use them. LangChain is designed to be modular and extensible, allowing developers to easily add new functionality and integrate with other systems.

# How it workss?

# session exam(data) --> langchain agent -> llm model --> integrity report

# integrity_score : 85
# risk level:low
# face presence ratio: 98
# browser events:
# tab_switch : 2
# focus_loss : 1
# copy_attempt : 0
# paste_attempt : 0


# LLM will generate a readable report on our examguard session

# Session Intergrity Report:

# The session recorded an integrity score of 85 with low risk level 
# face presence ratio was maintained for approx 98% of the exam duration
# two tab switches and one focus loss event were recorded during the session.
# no copy or paste attempts were detected, indicating that the candidate maintained a high level of integrity throughout the exam. Overall, the session demonstrates a strong commitment to academic honesty and adherence to exam guidelines.


# Rules
# You are an examination integrity reporting assistant.

# Analyze the provided session evidence.

# Explain:
# 1. Integrity score
# 2. Risk level
# 3. Face presence
# 4. Browser events
# 5. Important observations

# Do not invent events.

# Do not change the calculated score.

# Do not state that suspicious activity proves misconduct.

# Use cautious, evidence-based language.