"""
course.py
---------
The Course class: one subject the student has to prepare for.

A course knows how to calculate its own priority from three things:
    1. How close the deadline is   (urgency)
    2. How hard the course is      (difficulty)
    3. How many hours are needed   (workload)
"""

from datetime import date, datetime

DATE_FORMAT = "%Y-%m-%d"

# Points for each difficulty level.
DIFFICULTY_POINTS = {"Low": 1, "Medium": 2, "High": 3}

# Urgency counts double, because a close deadline matters most.
URGENCY_WEIGHT = 2

# Score thresholds (the score ranges from 4 to 12).
HIGH_THRESHOLD = 9
MEDIUM_THRESHOLD = 6


def parse_date(text):
    """Turn a string like '2026-10-09' into a date object."""
    return datetime.strptime(text.strip(), DATE_FORMAT).date()


class Course:
    def __init__(self, name, difficulty, exam_date, study_hours):
        name = name.strip()
        difficulty = difficulty.strip().title()

        if not name:
            raise ValueError("Course name cannot be empty.")
        if difficulty not in DIFFICULTY_POINTS:
            raise ValueError("Difficulty must be Low, Medium or High.")
        if study_hours <= 0:
            raise ValueError("Study hours must be greater than 0.")

        self.name = name
        self.difficulty = difficulty
        self.exam_date = exam_date          # a datetime.date object
        self.study_hours = study_hours      # total hours needed

    # ------------------------------------------------------------------
    # Priority calculation
    # ------------------------------------------------------------------
    def days_remaining(self, today=None):
        """Number of days from `today` until the exam/assignment."""
        today = today or date.today()
        return (self.exam_date - today).days

    def priority_score(self, today=None, hours_left=None):
        """
        Priority score = urgency x 2 + difficulty + workload   (range 4-12)

        urgency   : 3 if <= 3 days left, 2 if <= 7 days, otherwise 1
        difficulty: Low = 1, Medium = 2, High = 3
        workload  : 1 if <= 4 hours, 2 if <= 8 hours, otherwise 3

        `hours_left` lets the planner re-score a course after some of its
        hours have already been scheduled.
        """
        days = self.days_remaining(today)
        hours = self.study_hours if hours_left is None else hours_left

        if days <= 3:
            urgency = 3
        elif days <= 7:
            urgency = 2
        else:
            urgency = 1

        if hours <= 4:
            workload = 1
        elif hours <= 8:
            workload = 2
        else:
            workload = 3

        return urgency * URGENCY_WEIGHT + DIFFICULTY_POINTS[self.difficulty] + workload

    def priority(self, today=None, hours_left=None):
        """Return 'HIGH', 'MEDIUM' or 'LOW'."""
        score = self.priority_score(today, hours_left)
        if score >= HIGH_THRESHOLD:
            return "HIGH"
        if score >= MEDIUM_THRESHOLD:
            return "MEDIUM"
        return "LOW"

    # ------------------------------------------------------------------
    # Display and saving
    # ------------------------------------------------------------------
    def describe(self, today=None):
        """Multi-line description of the course, including its priority."""
        days = self.days_remaining(today)
        days_text = str(days) if days >= 0 else f"{days} (already passed)"
        return (
            f"{self.name}\n"
            f"  Difficulty: {self.difficulty}\n"
            f"  Exam date: {self.exam_date.isoformat()}\n"
            f"  Days Remaining: {days_text}\n"
            f"  Required Hours: {self.study_hours:g}\n"
            f"  Priority: {self.priority(today)}"
        )

    def to_dict(self):
        """Convert to a plain dictionary so it can be saved as JSON.
        (Priority is NOT saved: it changes every day, so we recalculate it.)"""
        return {
            "name": self.name,
            "difficulty": self.difficulty,
            "exam_date": self.exam_date.isoformat(),
            "study_hours": self.study_hours,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Course from a dictionary loaded from JSON."""
        return cls(
            name=data["name"],
            difficulty=data["difficulty"],
            exam_date=parse_date(data["exam_date"]),
            study_hours=float(data["study_hours"]),
        )

    def __str__(self):
        return f"{self.name} ({self.difficulty}, exam {self.exam_date.isoformat()})"
