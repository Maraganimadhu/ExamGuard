"""
ExamGuard - Examination Questions Bank
Domain: Python Core, Data Structures, OOP, and Logic
"""

EXAM_QUESTIONS = [
    {
        "id": 1,
        "domain": "Python Core & Syntax",
        "points": "1.0 Mark",
        "title": "What is the output of the following Python code snippet?",
        "code": "x = 10\nprint(x + 5)",
        "options": [
            {"key": "A", "val": "10"},
            {"key": "B", "val": "15"},
            {"key": "C", "val": "20"},
            {"key": "D", "val": "25"}
        ],
        "correct": "B"
    },
    {
        "id": 2,
        "domain": "Data Structures & Slicing",
        "points": "1.0 Mark",
        "title": "What will be printed by the following list slicing operation?",
        "code": "nums = [10, 20, 30, 40, 50]\nprint(nums[1:4])",
        "options": [
            {"key": "A", "val": "[10, 20, 30]"},
            {"key": "B", "val": "[20, 30, 40]"},
            {"key": "C", "val": "[20, 30, 40, 50]"},
            {"key": "D", "val": "[30, 40]"}
        ],
        "correct": "B"
    },
    {
        "id": 3,
        "domain": "Dictionaries & Mapping",
        "points": "1.0 Mark",
        "title": "What does the dictionary get() method return if the key is not found and no default is provided?",
        "code": "user = {'name': 'Alice'}\nprint(user.get('age'))",
        "options": [
            {"key": "A", "val": "KeyError"},
            {"key": "B", "val": "None"},
            {"key": "C", "val": "0"},
            {"key": "D", "val": "False"}
        ],
        "correct": "B"
    },
    {
        "id": 4,
        "domain": "Data Types & Mutability",
        "points": "1.0 Mark",
        "title": "Which of the following built-in collection types in Python is immutable?",
        "code": "# Cannot be modified in-place after creation\nmy_data = (1, 2, 3)",
        "options": [
            {"key": "A", "val": "List"},
            {"key": "B", "val": "Dictionary"},
            {"key": "C", "val": "Tuple"},
            {"key": "D", "val": "Set"}
        ],
        "correct": "C"
    },
    {
        "id": 5,
        "domain": "Functions & Default Arguments",
        "points": "1.0 Mark",
        "title": "What is the output of calling this function with a single argument?",
        "code": "def multiply(a, b=2):\n    return a * b\n\nprint(multiply(4))",
        "options": [
            {"key": "A", "val": "4"},
            {"key": "B", "val": "8"},
            {"key": "C", "val": "TypeError"},
            {"key": "D", "val": "16"}
        ],
        "correct": "B"
    },
    {
        "id": 6,
        "domain": "List Comprehension",
        "points": "1.0 Mark",
        "title": "What is the output of the following list comprehension expression?",
        "code": "squares = [x**2 for x in range(5) if x % 2 == 0]\nprint(squares)",
        "options": [
            {"key": "A", "val": "[0, 4, 16]"},
            {"key": "B", "val": "[1, 9]"},
            {"key": "C", "val": "[0, 1, 4, 9, 16]"},
            {"key": "D", "val": "[4, 16]"}
        ],
        "correct": "A"
    },
    {
        "id": 7,
        "domain": "Object-Oriented Programming",
        "points": "1.0 Mark",
        "title": "Which method in Python serves as the object constructor/initializer?",
        "code": "class Candidate:\n    def __init__(self, name):\n        self.name = name",
        "options": [
            {"key": "A", "val": "__construct__()"},
            {"key": "B", "val": "__init__()"},
            {"key": "C", "val": "__new__()"},
            {"key": "D", "val": "__main__()"}
        ],
        "correct": "B"
    },
    {
        "id": 8,
        "domain": "Exception Handling",
        "points": "1.0 Mark",
        "title": "Which block in Python always executes regardless of whether an exception occurs?",
        "code": "try:\n    perform_task()\nexcept ValueError:\n    handle_error()\nfinally:\n    cleanup()",
        "options": [
            {"key": "A", "val": "finally"},
            {"key": "B", "val": "else"},
            {"key": "C", "val": "catch"},
            {"key": "D", "val": "ensure"}
        ],
        "correct": "A"
    },
    {
        "id": 9,
        "domain": "String Manipulation",
        "points": "1.0 Mark",
        "title": "What is the result of using strip() on a string with whitespace on both ends?",
        "code": "text = '  ExamGuard Secure  '\nprint(text.strip())",
        "options": [
            {"key": "A", "val": "'ExamGuard'"},
            {"key": "B", "val": "'ExamGuard Secure'"},
            {"key": "C", "val": "'ExamGuardSecure'"},
            {"key": "D", "val": "'  ExamGuard Secure'"}
        ],
        "correct": "B"
    },
    {
        "id": 10,
        "domain": "Iterators & Generators",
        "points": "1.0 Mark",
        "title": "Which Python keyword produces a generator by yielding values one at a time?",
        "code": "def count_up(n):\n    for i in range(n):\n        yield i",
        "options": [
            {"key": "A", "val": "return"},
            {"key": "B", "val": "yield"},
            {"key": "C", "val": "emit"},
            {"key": "D", "val": "send"}
        ],
        "correct": "B"
    }
]

QUESTION_KEY_MAP = {q["id"]: q["correct"] for q in EXAM_QUESTIONS}
