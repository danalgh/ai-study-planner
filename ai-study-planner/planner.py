"""
planner.py
----------
The Planner class holds the student and their courses, builds the study
plan, and saves/loads everything to a JSON file.

HOW THE PLAN IS BUILT (the algorithm)
-------------------------------------
For every study day, starting today:
  1. The day has `hours_per_day` hours to hand out, one hour (block) at a time.
  2. For each block, pick the course with the highest priority score.
     (Scores are recalculated each time, using the hours still unscheduled,
     so the plan adapts as the exam gets closer.)
     Ties are broken by "pace": hours left / days left before the exam.
  3. Variety rule: no course may take more than half of a day (rounded up),
     so the student doesn't study one subject all day. The rule is lifted
     for a course that could not finish before its exam otherwise, and any
     leftover time is given out even if only one course remains.
  4. A course is never scheduled on or after its exam date.
Anything that doesn't fit becomes a warning.
"""

import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path

from course import Course
from student import Student

BLOCK_HOURS = 1.0   # the plan is built one block of study at a time
EPSILON = 1e-9      # tiny number used when comparing decimals


def hours_text(hours):
    """1 -> '1 hour', 2 -> '2 hours', 1.5 -> '1.5 hours'."""
    label = "hour" if abs(hours - 1) < EPSILON else "hours"
    return f"{hours:g} {label}"


class Planner:
    def __init__(self):
        self.student = None
        self.courses = []     # list of Course objects
        self.plan = []        # list of {"date": "YYYY-MM-DD", "sessions": {course: hours}}
        self.warnings = []    # list of strings
        self.unsaved = False  # True when there are changes not yet saved to file

    # ------------------------------------------------------------------
    # Student and courses
    # ------------------------------------------------------------------
    def _changed(self):
        """Any change to the inputs makes the old plan out of date."""
        self.plan = []
        self.warnings = []
        self.unsaved = True

    def set_student(self, student):
        self.student = student
        self._changed()

    def find_course(self, name):
        for course in self.courses:
            if course.name.lower() == name.strip().lower():
                return course
        return None

    def add_course(self, course):
        if self.find_course(course.name):
            raise ValueError(f"'{course.name}' is already in your list.")
        self.courses.append(course)
        self._changed()

    def remove_course(self, name):
        course = self.find_course(name)
        if course is None:
            return False
        self.courses.remove(course)
        self._changed()
        return True

    def ranked_courses(self, today=None):
        """Courses sorted from highest to lowest priority."""
        return sorted(
            self.courses,
            key=lambda c: (-c.priority_score(today), c.exam_date),
        )

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------
    def generate_plan(self, start_date=None):
        """Build the study plan. Stores it in self.plan and returns it."""
        if self.student is None:
            raise ValueError("Enter the student information first.")
        if not self.courses:
            raise ValueError("Add at least one course first.")

        start = start_date or date.today()
        hours_per_day = self.student.hours_per_day
        plan_days = self.student.study_days
        max_per_course = math.ceil(hours_per_day / 2)   # the "variety" cap

        remaining = {c.name: c.study_hours for c in self.courses}
        plan = []

        for day_index in range(plan_days):
            today = start + timedelta(days=day_index)
            days_left_in_plan = plan_days - day_index
            sessions = {}                 # course name -> hours today
            free = float(hours_per_day)   # hours still unassigned today

            # Pass 1 respects the variety cap. Pass 2 (no cap) fills any
            # time that is still free.
            for cap in (max_per_course, None):
                while free > EPSILON:
                    course = self._pick_course(
                        today, remaining, sessions, cap, days_left_in_plan
                    )
                    if course is None:
                        break

                    done = sessions.get(course.name, 0.0)
                    allowed = self._allowed_today(
                        course, today, remaining[course.name], done, cap, days_left_in_plan
                    )
                    block = min(BLOCK_HOURS, remaining[course.name], free, allowed)

                    sessions[course.name] = round(done + block, 2)
                    remaining[course.name] = round(remaining[course.name] - block, 2)
                    free = round(free - block, 2)

            plan.append({"date": today.isoformat(), "sessions": sessions})

        self.plan = plan
        self.warnings = self._build_warnings(remaining, start, plan_days)
        self.unsaved = True
        return plan

    def _usable_days(self, course, today, days_left_in_plan):
        """Study days left (counting today) before the exam or the plan ends."""
        return min(course.days_remaining(today), days_left_in_plan)

    def _allowed_today(self, course, today, left, done, cap, days_left_in_plan):
        """How many more hours this course may get today.

        Normally that is whatever is left of the variety cap. But if the course
        could not be finished even at the cap every remaining day, the cap is
        lifted so the course doesn't miss its exam."""
        if cap is None:
            return math.inf

        room_today = cap - done
        usable_days = self._usable_days(course, today, days_left_in_plan)
        most_under_cap = room_today + cap * (usable_days - 1)

        if left > most_under_cap + EPSILON:
            return math.inf
        return room_today

    def _pick_course(self, today, remaining, sessions, cap, days_left_in_plan):
        """Choose which course gets the next block of study time."""
        best_course = None
        best_key = None

        for course in self.courses:
            left = remaining[course.name]
            if left <= EPSILON or course.days_remaining(today) < 1:
                continue    # nothing left to study, or the exam is here/past

            done = sessions.get(course.name, 0.0)
            allowed = self._allowed_today(
                course, today, left, done, cap, days_left_in_plan
            )
            if allowed <= EPSILON:
                continue    # this course already has its share today

            usable_days = self._usable_days(course, today, days_left_in_plan)
            pace = left / usable_days
            key = (course.priority_score(today, left), pace)

            if best_key is None or key > best_key:
                best_course, best_key = course, key

        return best_course

    def _build_warnings(self, remaining, start, plan_days):
        warnings = []
        for course in self.courses:
            left = remaining[course.name]
            if left <= EPSILON:
                continue

            days_to_exam = course.days_remaining(start)
            if days_to_exam < 1:
                reason = "the exam date has already passed (or is today)"
            elif days_to_exam > plan_days:
                reason = "your plan ends before the exam: add more study days"
            else:
                reason = "there are not enough free hours: add hours per day"

            warnings.append(
                f"{course.name}: {left:g} of {course.study_hours:g} hours "
                f"could not be scheduled because {reason}."
            )
        return warnings

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def format_plan(self):
        """Return the study plan as readable text."""
        if not self.plan:
            return "No study plan yet. Generate one first."

        lines = [
            f"Study plan for {self.student.name}",
            f"{self.student.hours_per_day:g}h/day for {self.student.study_days} day(s)",
            "",
        ]
        planned_total = 0.0

        for day in self.plan:
            day_date = date.fromisoformat(day["date"])
            lines.append(day_date.strftime("%A, %d %b %Y"))

            if not day["sessions"]:
                lines.append("  - Free day")
            for course_name, hours in day["sessions"].items():
                lines.append(f"  - {course_name}: {hours_text(hours)}")
                planned_total += hours
            lines.append("")

        needed_total = sum(c.study_hours for c in self.courses)
        lines.append(f"Scheduled {planned_total:g} of {needed_total:g} required hours.")

        for warning in self.warnings:
            lines.append(f"WARNING - {warning}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Save and load
    # ------------------------------------------------------------------
    def save(self, path):
        """Write the student, courses and plan to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "saved_on": datetime.now().isoformat(timespec="seconds"),
            "student": self.student.to_dict() if self.student else None,
            "courses": [c.to_dict() for c in self.courses],
            "plan": self.plan,
            "warnings": self.warnings,
        }
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        self.unsaved = False

    def load(self, path):
        """Replace the current data with the contents of a JSON file.
        Raises FileNotFoundError or ValueError if the file can't be used."""
        with open(Path(path), encoding="utf-8") as file:
            data = json.load(file)

        try:
            student = Student.from_dict(data["student"]) if data.get("student") else None
            courses = [Course.from_dict(item) for item in data.get("courses", [])]
            plan = list(data.get("plan", []))
            warnings = list(data.get("warnings", []))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"The save file is damaged ({error}).") from error

        self.student = student
        self.courses = courses
        self.plan = plan
        self.warnings = warnings
        self.unsaved = False
