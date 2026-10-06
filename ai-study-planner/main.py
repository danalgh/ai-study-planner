"""
main.py
-------
The text menu of the AI Study Planner. Run it with:

    python main.py
"""

from datetime import date
from pathlib import Path

from course import Course, parse_date
from planner import Planner
from student import Student

DATA_FILE = Path(__file__).resolve().parent / "data" / "courses.json"


# ----------------------------------------------------------------------
# Input helpers: keep asking until the answer is valid
# ----------------------------------------------------------------------
def ask_text(prompt):
    while True:
        answer = input(prompt).strip()
        if answer:
            return answer
        print("  This cannot be empty.")


def ask_number(prompt, minimum, maximum=None, whole=False):
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw) if whole else float(raw)
        except ValueError:
            print("  Please enter a number.")
            continue

        if value < minimum or (maximum is not None and value > maximum):
            limit = f"at least {minimum:g}" if maximum is None else f"between {minimum:g} and {maximum:g}"
            print(f"  Please enter a value {limit}.")
            continue
        return value


def ask_future_date(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            value = parse_date(raw)
        except ValueError:
            print("  Use the format YYYY-MM-DD, for example 2026-12-15.")
            continue

        if value <= date.today():
            print("  The date must be in the future.")
            continue
        return value


def ask_difficulty():
    choices = {
        "1": "Low", "low": "Low", "l": "Low",
        "2": "Medium", "medium": "Medium", "m": "Medium",
        "3": "High", "high": "High", "h": "High",
    }
    print("  Difficulty:  1) Low   2) Medium   3) High")
    while True:
        raw = input("  Choose 1-3: ").strip().lower()
        if raw in choices:
            return choices[raw]
        print("  Please choose 1, 2 or 3.")


def ask_yes_no(prompt):
    return input(prompt).strip().lower() in ("y", "yes")


# ----------------------------------------------------------------------
# Menu actions
# ----------------------------------------------------------------------
def set_student(planner):
    print("\n--- Student information ---")
    if planner.student:
        print(f"Current: {planner.student}")

    name = ask_text("Student name: ")
    hours = ask_number("Study hours available per day: ", 0.5, 24)
    days = ask_number("Number of study days: ", 1, whole=True)

    had_plan = bool(planner.plan)
    planner.set_student(Student(name, hours, days))
    print(f"Saved in memory: {planner.student}")
    if had_plan:
        print("Note: your old study plan was cleared. Generate a new one (option 5).")


def add_course(planner):
    print("\n--- Add a course ---")
    name = ask_text("Course name: ")
    if planner.find_course(name):
        print(f"'{name}' is already in your list.")
        return

    difficulty = ask_difficulty()
    exam_date = ask_future_date("Exam/assignment date (YYYY-MM-DD): ")
    hours = ask_number("Estimated study hours needed: ", 0.5)

    had_plan = bool(planner.plan)
    course = Course(name, difficulty, exam_date, hours)
    planner.add_course(course)
    print(f"Added. Priority: {course.priority()}")
    if had_plan:
        print("Note: your old study plan was cleared. Generate a new one (option 5).")


def view_courses(planner):
    print("\n--- Courses (highest priority first) ---")
    if not planner.courses:
        print("No courses yet. Add one with option 2.")
        return
    for course in planner.ranked_courses():
        print(course.describe())
        print()


def remove_course(planner):
    print("\n--- Remove a course ---")
    if not planner.courses:
        print("No courses to remove.")
        return

    for course in planner.courses:
        print(f"  - {course.name}")
    name = ask_text("Name of the course to remove: ")

    had_plan = bool(planner.plan)
    if planner.remove_course(name):
        print(f"Removed '{name}'.")
        if had_plan:
            print("Note: your old study plan was cleared. Generate a new one (option 5).")
    else:
        print("No course with that name.")


def generate_plan(planner):
    if planner.student is None:
        print("\nPlease enter the student information first (option 1).")
        return
    if not planner.courses:
        print("\nPlease add at least one course first (option 2).")
        return

    planner.generate_plan()
    print()
    print(planner.format_plan())


def view_plan(planner):
    print()
    print(planner.format_plan())


def save_data(planner):
    try:
        planner.save(DATA_FILE)
        print(f"\nSaved to {DATA_FILE}")
    except OSError as error:
        print(f"\nCould not save the file: {error}")


def load_data(planner):
    try:
        planner.load(DATA_FILE)
        print(f"\nLoaded {len(planner.courses)} course(s) from {DATA_FILE}")
    except FileNotFoundError:
        print("\nNo saved file found yet. Save something first (option 7).")
    except (OSError, ValueError) as error:
        print(f"\nCould not load the file: {error}")


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
MENU = """
===== AI Study Planner =====
1. Student information
2. Add a course
3. View courses (by priority)
4. Remove a course
5. Generate study plan
6. View current plan
7. Save to file
8. Load from file
0. Exit
"""

ACTIONS = {
    "1": set_student,
    "2": add_course,
    "3": view_courses,
    "4": remove_course,
    "5": generate_plan,
    "6": view_plan,
    "7": save_data,
    "8": load_data,
}


def main():
    planner = Planner()

    if DATA_FILE.exists():
        try:
            planner.load(DATA_FILE)
            print(f"Loaded your saved data from {DATA_FILE.name}.")
        except (OSError, ValueError) as error:
            print(f"Could not load saved data: {error}")

    try:
        while True:
            print(MENU)
            choice = input("Choose an option: ").strip()

            if choice == "0":
                if planner.unsaved and ask_yes_no("You have unsaved changes. Save now? (y/n): "):
                    save_data(planner)
                print("Good luck with your studies!")
                break

            action = ACTIONS.get(choice)
            if action is None:
                print("Please choose a number from the menu.")
            else:
                action(planner)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
