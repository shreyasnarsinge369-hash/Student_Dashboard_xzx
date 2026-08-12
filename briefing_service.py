"""Local intelligence for the SHREYAS OS daily command briefing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from database import Habit, Task


@dataclass(frozen=True)
class DailyBriefing:
    """A concise, actionable summary generated from dashboard data."""

    headline: str
    summary: str
    focus_items: tuple[str, ...]


def build_daily_briefing(
    today: date,
    tasks: list[Task],
    calendar_events: pd.DataFrame,
    subject_breakdown: pd.DataFrame,
    weekly_workouts: pd.DataFrame,
    habits: list[Habit],
) -> DailyBriefing:
    """Turn the dashboard's current state into a clear, local action plan."""
    incomplete_high_priority = [task.name for task in tasks if not task.completed and task.priority == "High"]
    incomplete_tasks = [task.name for task in tasks if not task.completed]
    study_hours = float(subject_breakdown["Hours"].sum())
    today_minutes = int(
        weekly_workouts.loc[weekly_workouts["Day"] == today.strftime("%a"), "Minutes"].sum()
    )
    incomplete_habits = [habit.name for habit in habits if not habit.completed]

    focus_items: list[str] = []
    if incomplete_high_priority:
        focus_items.append(f"Start with {incomplete_high_priority[0]}; it is your highest-priority open task.")
    elif incomplete_tasks:
        focus_items.append(f"Clear {incomplete_tasks[0]} to create early momentum.")
    else:
        focus_items.append("Your task board is clear. Protect time for your most valuable work.")

    if not calendar_events.empty:
        first_event = calendar_events.iloc[0]
        focus_items.append(f"Next on the calendar: {first_event['Event']} at {first_event['Time']}.")

    if study_hours < 2:
        focus_items.append("Log one focused study block to move toward a 2-hour baseline.")
    elif study_hours < 4:
        focus_items.append(f"You have {study_hours:g} study hours logged; one more deep-work block would make today strong.")

    if today_minutes == 0:
        focus_items.append("Schedule a workout window before the day gets crowded.")
    if incomplete_habits:
        focus_items.append(f"Keep your streaks alive: {incomplete_habits[0]} is still open.")

    focus_items = focus_items[:3]
    completed_tasks = len(tasks) - len(incomplete_tasks)
    if not incomplete_tasks and study_hours >= 2 and today_minutes > 0:
        headline = "You are operating with momentum."
    elif incomplete_high_priority:
        headline = "Your priority is clear."
    else:
        headline = "Build a focused first win."

    summary = (
        f"{completed_tasks}/{len(tasks)} tasks complete | "
        f"{study_hours:g}h study | {today_minutes}m workout"
    )
    return DailyBriefing(headline, summary, tuple(focus_items))
