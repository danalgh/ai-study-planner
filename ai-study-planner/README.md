# AI Study Planner

A command-line app that turns your courses, exam dates and available time into a day-by-day study plan. Pure Python, no installs needed (Python 3.8+).

## Run it

```bash
python main.py
```

On start-up the app loads `data/courses.json` if it exists. That file ships with sample data (exam dates are relative to when it was created, so they will be in the past after a while). Just add your own courses, or delete the file to start fresh.

## Project structure

```
ai-study-planner/
├── main.py          # text menu + input validation
├── student.py       # Student class (name, hours/day, study days)
├── course.py        # Course class (+ priority calculation)
├── planner.py       # Planner class (plan algorithm, save/load)
├── data/
│   └── courses.json # saved student, courses and plan
├── README.md
└── requirements.txt
```

## How priority is calculated

`score = urgency x 2 + difficulty + workload` (range 4-12)

| Factor     | 1 point      | 2 points    | 3 points   |
|------------|--------------|-------------|------------|
| Urgency    | > 7 days     | 4-7 days    | <= 3 days  |
| Difficulty | Low          | Medium      | High       |
| Workload   | <= 4 hours   | 5-8 hours   | > 8 hours  |

Score 9+ is **HIGH**, 6-8 is **MEDIUM**, below 6 is **LOW**.

```
Artificial Intelligence
  Difficulty: High          -> 3
  Days Remaining: 3         -> 3 x 2 = 6
  Required Hours: 8         -> 2
  Priority: HIGH            -> 11
```

Priority is recalculated every time and never saved, because it changes as the exam gets closer.

## How the plan is built

For each study day, starting today, the planner hands out the day's hours one hour at a time:

1. Pick the course with the highest priority score (re-scored using the hours still unscheduled).
2. **Variety rule:** no course gets more than half the day, so you don't study one subject for hours. The rule is lifted automatically if a course couldn't finish before its exam otherwise.
3. Never schedule a course on or after its exam date.
4. Anything that doesn't fit is reported as a warning, with the reason (plan too short, not enough hours per day, or exam already passed).

## Example output

```
Tuesday, 06 Oct 2026
  - Artificial Intelligence: 3 hours

Thursday, 08 Oct 2026
  - Artificial Intelligence: 2 hours
  - Java: 1 hour

Friday, 09 Oct 2026
  - SQL: 2 hours
  - Java: 1 hour
```

## Concepts practised

- **Classes / OOP:** `Student`, `Course`, `Planner`, with `__init__`, methods, properties, `@classmethod`
- **Lists and dictionaries:** the course list, the plan (`{course: hours}` per day), JSON conversion
- **File handling:** saving and loading JSON with `pathlib` and `json`
- **Date/time:** `date`, `timedelta`, `strftime`
- **Algorithms:** scoring, sorting with a key, greedy scheduling
- **Error handling:** input validation loops and `try/except`

## Ideas to extend it

- Let the user pick the start date or skip weekends
- Add a manual "importance" boost per course
- Mark sessions as done and re-plan the rest
- Export the plan to a calendar (`.ics`) file
- Build a GUI (Tkinter) or web version (Flask)
