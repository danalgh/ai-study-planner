"""
student.py
----------
The Student class: who is studying, and how much time they have.
"""


class Student:
    def __init__(self, name, hours_per_day, study_days):
        name = name.strip()

        if not name:
            raise ValueError("Student name cannot be empty.")
        if not 0 < hours_per_day <= 24:
            raise ValueError("Hours per day must be between 0 and 24.")
        if study_days < 1:
            raise ValueError("Study days must be at least 1.")

        self.name = name
        self.hours_per_day = hours_per_day
        self.study_days = int(study_days)

    @property
    def total_hours(self):
        """Total study time available across all days."""
        return self.hours_per_day * self.study_days

    def to_dict(self):
        return {
            "name": self.name,
            "hours_per_day": self.hours_per_day,
            "study_days": self.study_days,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            hours_per_day=float(data["hours_per_day"]),
            study_days=int(data["study_days"]),
        )

    def __str__(self):
        return (
            f"{self.name}: {self.hours_per_day:g}h/day "
            f"for {self.study_days} day(s) ({self.total_hours:g}h in total)"
        )
