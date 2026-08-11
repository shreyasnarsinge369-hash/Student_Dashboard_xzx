"""Local persistence for SHREYAS OS.

This module owns SQLite setup and task queries, keeping database details out of
the Streamlit UI layer.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("shreyas_os.db")


@dataclass(frozen=True)
class Task:
    """A task displayed in the dashboard."""

    id: int
    name: str
    priority: str
    completed: bool


@dataclass(frozen=True)
class StudySession:
    """One focused study session recorded by the user."""

    id: int
    subject: str
    duration_minutes: int
    study_date: date


@dataclass(frozen=True)
class WorkoutSession:
    """One workout recorded by the user."""

    id: int
    workout_type: str
    duration_minutes: int
    distance_km: float
    workout_date: date


DEFAULT_TASKS = (
    ("Backend Development", "High"),
    ("Workout", "Medium"),
    ("Mathematics Revision", "High"),
    ("Batcomputer Development", "Low"),
)


def get_connection() -> sqlite3.Connection:
    """Create a short-lived SQLite connection with named columns enabled."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create the database table when the dashboard is first opened."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_date TEXT NOT NULL,
                name TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_date, name)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
                study_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS initialized_days (
                task_date TEXT PRIMARY KEY,
                initialized_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_type TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
                distance_km REAL NOT NULL DEFAULT 0 CHECK (distance_km >= 0),
                workout_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def ensure_daily_tasks(task_date: date) -> None:
    """Seed starter tasks once per day without overwriting user progress."""
    task_date_value = task_date.isoformat()
    with get_connection() as connection:
        initialized = connection.execute(
            "INSERT OR IGNORE INTO initialized_days (task_date) VALUES (?)",
            (task_date_value,),
        )
        if initialized.rowcount == 0:
            return
        connection.executemany(
            """
            INSERT OR IGNORE INTO tasks (task_date, name, priority)
            VALUES (?, ?, ?)
            """,
            [(task_date_value, name, priority) for name, priority in DEFAULT_TASKS],
        )


def get_tasks_for_date(task_date: date) -> list[Task]:
    """Return a day's tasks in priority order."""
    priority_order = "CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END"
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, name, priority, completed
            FROM tasks
            WHERE task_date = ?
            ORDER BY completed ASC, {priority_order}, id ASC
            """,
            (task_date.isoformat(),),
        ).fetchall()

    return [
        Task(
            id=row["id"],
            name=row["name"],
            priority=row["priority"],
            completed=bool(row["completed"]),
        )
        for row in rows
    ]


def set_task_completion(task_id: int, completed: bool) -> None:
    """Persist a checkbox change from the dashboard."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (int(completed), task_id),
        )


def add_task(task_date: date, name: str, priority: str) -> bool:
    """Add a task, returning False when the same task already exists that day."""
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO tasks (task_date, name, priority)
                VALUES (?, ?, ?)
                """,
                (task_date.isoformat(), name.strip(), priority),
            )
    except sqlite3.IntegrityError:
        return False
    return True


def delete_task(task_id: int) -> None:
    """Remove a task selected by the user."""
    with get_connection() as connection:
        connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def add_study_session(study_date: date, subject: str, duration_minutes: int) -> None:
    """Store a completed study session."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO study_sessions (subject, duration_minutes, study_date)
            VALUES (?, ?, ?)
            """,
            (subject.strip(), duration_minutes, study_date.isoformat()),
        )


def get_study_subject_breakdown(study_date: date) -> list[tuple[str, int]]:
    """Return each subject's minutes for a single day."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT subject, SUM(duration_minutes) AS minutes
            FROM study_sessions
            WHERE study_date = ?
            GROUP BY subject
            ORDER BY minutes DESC, subject ASC
            """,
            (study_date.isoformat(),),
        ).fetchall()
    return [(row["subject"], row["minutes"]) for row in rows]


def get_study_minutes_between(start_date: date, end_date: date) -> dict[date, int]:
    """Return daily study minutes for an inclusive date range."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT study_date, SUM(duration_minutes) AS minutes
            FROM study_sessions
            WHERE study_date BETWEEN ? AND ?
            GROUP BY study_date
            """,
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()
    return {date.fromisoformat(row["study_date"]): row["minutes"] for row in rows}


def get_study_streak(today: date) -> int:
    """Count consecutive study days ending today."""
    daily_minutes = get_study_minutes_between(today - timedelta(days=365), today)
    streak = 0
    cursor = today
    while daily_minutes.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def add_workout_session(
    workout_date: date,
    workout_type: str,
    duration_minutes: int,
    distance_km: float,
) -> None:
    """Store a completed workout session."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO workout_sessions (
                workout_type, duration_minutes, distance_km, workout_date
            )
            VALUES (?, ?, ?, ?)
            """,
            (workout_type, duration_minutes, distance_km, workout_date.isoformat()),
        )


def get_workout_totals_between(start_date: date, end_date: date) -> dict[date, tuple[int, float]]:
    """Return duration and distance totals for every logged workout day."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                workout_date,
                SUM(duration_minutes) AS minutes,
                SUM(distance_km) AS distance_km
            FROM workout_sessions
            WHERE workout_date BETWEEN ? AND ?
            GROUP BY workout_date
            """,
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()
    return {
        date.fromisoformat(row["workout_date"]): (row["minutes"], row["distance_km"])
        for row in rows
    }


def get_workout_streak(today: date) -> int:
    """Count consecutive workout days ending today."""
    daily_workouts = get_workout_totals_between(today - timedelta(days=365), today)
    streak = 0
    cursor = today
    while daily_workouts.get(cursor, (0, 0.0))[0] > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
