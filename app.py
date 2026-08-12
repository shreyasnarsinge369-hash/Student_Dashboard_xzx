from __future__ import annotations

from datetime import datetime, timedelta
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from briefing_service import build_daily_briefing
from calendar_service import (
    CalendarSetupError,
    connect_google_calendar,
    get_upcoming_events,
    is_calendar_authorized,
    is_calendar_configured,
)
from database import (
    Task,
    add_study_session,
    add_task,
    add_workout_session,
    add_habit,
    delete_habit,
    delete_task,
    ensure_daily_tasks,
    get_day_summary,
    get_habit_streak,
    get_habits_for_date,
    get_study_minutes_between,
    get_study_streak,
    get_study_subject_breakdown,
    get_tasks_for_date,
    get_workout_streak,
    get_workout_totals_between,
    initialize_database,
    set_habit_completion,
    set_task_completion,
)


APP_OWNER = "Shreyas"


def configure_page() -> None:
    """Configure Streamlit before rendering any page content."""
    st.set_page_config(
        page_title="SHREYAS OS",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def inject_css() -> None:
    """Add the dashboard visual system with a dark glassmorphism style."""
    st.markdown(
        """
        <style>
            :root {
                --bg: #050812;
                --panel: rgba(12, 20, 36, 0.72);
                --panel-strong: rgba(14, 25, 45, 0.9);
                --border: rgba(125, 211, 252, 0.18);
                --border-bright: rgba(34, 211, 238, 0.4);
                --text: #edf7ff;
                --muted: #93a9bd;
                --soft: #5f7488;
                --cyan: #22d3ee;
                --blue: #38bdf8;
                --green: #34d399;
                --amber: #fbbf24;
                --red: #fb7185;
            }

            html, body, [class*="css"] {
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .stApp {
                color: var(--text);
                background:
                    radial-gradient(circle at 14% 12%, rgba(34, 211, 238, 0.12), transparent 28rem),
                    radial-gradient(circle at 86% 4%, rgba(56, 189, 248, 0.11), transparent 24rem),
                    linear-gradient(135deg, #050812 0%, #07111f 48%, #050812 100%);
            }

            .block-container {
                max-width: 1380px;
                padding: 2.4rem 2.2rem 3rem;
            }

            [data-testid="stHeader"], [data-testid="stToolbar"] {
                background: transparent;
            }

            .os-shell {
                position: relative;
            }

            .os-shell::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                opacity: 0.12;
                background-image:
                    linear-gradient(rgba(125, 211, 252, 0.12) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(125, 211, 252, 0.12) 1px, transparent 1px);
                background-size: 72px 72px;
                mask-image: linear-gradient(to bottom, black, transparent 72%);
            }

            .hero {
                display: flex;
                justify-content: space-between;
                gap: 1.25rem;
                align-items: flex-end;
                padding: 1.45rem 1.55rem;
                margin-bottom: 1.25rem;
                border: 1px solid var(--border);
                border-radius: 22px;
                background: linear-gradient(135deg, rgba(10, 18, 32, 0.84), rgba(8, 18, 31, 0.58));
                box-shadow: 0 20px 70px rgba(0, 0, 0, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.06);
                backdrop-filter: blur(18px);
            }

            .brand-mark {
                width: 3.25rem;
                height: 3.25rem;
                display: grid;
                place-items: center;
                border: 1px solid var(--border-bright);
                border-radius: 16px;
                color: var(--cyan);
                background: rgba(34, 211, 238, 0.08);
                box-shadow: 0 0 34px rgba(34, 211, 238, 0.13);
                font-size: 1.2rem;
            }

            .title-row {
                display: flex;
                align-items: center;
                gap: 0.95rem;
            }

            .eyebrow {
                margin: 0 0 0.25rem;
                color: var(--cyan);
                font-size: 0.76rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 700;
            }

            .hero h1 {
                margin: 0;
                font-size: clamp(2.15rem, 4vw, 4rem);
                line-height: 0.94;
                letter-spacing: 0;
                font-weight: 800;
            }

            .subtitle {
                margin: 0.55rem 0 0;
                color: var(--muted);
                font-size: 1.02rem;
            }

            .status-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(7rem, 1fr));
                gap: 0.7rem;
                min-width: min(100%, 24rem);
            }

            .status-chip {
                padding: 0.85rem 0.9rem;
                border: 1px solid rgba(125, 211, 252, 0.16);
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.045);
            }

            .chip-label {
                display: block;
                color: var(--soft);
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 0.25rem;
            }

            .chip-value {
                color: var(--text);
                font-weight: 700;
                font-size: 0.98rem;
            }

            .glass-card {
                min-height: 100%;
                padding: 1.15rem;
                border: 1px solid var(--border);
                border-radius: 20px;
                background: linear-gradient(145deg, var(--panel), rgba(7, 14, 26, 0.62));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.055);
                backdrop-filter: blur(18px);
                transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
            }

            .glass-card:hover {
                transform: translateY(-2px);
                border-color: var(--border-bright);
                box-shadow: 0 22px 70px rgba(0, 0, 0, 0.34), 0 0 35px rgba(34, 211, 238, 0.08);
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                padding: 0.35rem;
                border: 1px solid var(--border);
                border-radius: 20px;
                background: linear-gradient(145deg, var(--panel), rgba(7, 14, 26, 0.62));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.055);
                backdrop-filter: blur(18px);
                transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
            }

            [data-testid="stVerticalBlockBorderWrapper"]:hover {
                transform: translateY(-2px);
                border-color: var(--border-bright);
                box-shadow: 0 22px 70px rgba(0, 0, 0, 0.34), 0 0 35px rgba(34, 211, 238, 0.08);
            }

            .card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 0.9rem;
            }

            .card-title {
                margin: 0;
                font-size: 1rem;
                font-weight: 800;
                letter-spacing: 0;
            }

            .card-icon {
                color: var(--cyan);
                opacity: 0.95;
                font-size: 1.05rem;
            }

            .briefing-card {
                margin-bottom: 1.25rem;
                padding: 1.2rem 1.35rem;
                border: 1px solid rgba(34, 211, 238, 0.26);
                border-radius: 16px;
                background: linear-gradient(110deg, rgba(8, 32, 48, 0.76), rgba(12, 20, 36, 0.72));
                box-shadow: inset 3px 0 0 var(--cyan), 0 14px 40px rgba(0, 0, 0, 0.2);
            }

            .briefing-label {
                color: var(--cyan);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.12em;
                text-transform: uppercase;
            }

            .briefing-headline {
                margin: 0.35rem 0 0.2rem;
                color: var(--text);
                font-size: 1.35rem;
                font-weight: 800;
            }

            .briefing-summary {
                margin: 0;
                color: var(--muted);
                font-size: 0.9rem;
            }

            .briefing-list {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.65rem;
                margin-top: 1rem;
            }

            .briefing-item {
                padding: 0.75rem 0.85rem;
                border: 1px solid rgba(125, 211, 252, 0.13);
                border-radius: 10px;
                color: var(--text);
                background: rgba(5, 16, 29, 0.44);
                font-size: 0.84rem;
                line-height: 1.45;
            }

            .metric-row {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.65rem;
                margin-bottom: 0.9rem;
            }

            .metric-tile {
                padding: 0.8rem;
                border-radius: 16px;
                border: 1px solid rgba(125, 211, 252, 0.12);
                background: rgba(255, 255, 255, 0.04);
            }

            .metric-label {
                color: var(--soft);
                font-size: 0.73rem;
                margin-bottom: 0.25rem;
            }

            .metric-value {
                color: var(--text);
                font-size: 1.35rem;
                font-weight: 800;
                line-height: 1;
            }

            .task-item, .calendar-row, .subject-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                padding: 0.74rem 0;
                border-bottom: 1px solid rgba(125, 211, 252, 0.09);
            }

            .task-item:last-child, .calendar-row:last-child, .subject-row:last-child {
                border-bottom: none;
            }

            [data-testid="stCheckbox"] {
                margin: 0.1rem 0;
                padding: 0.45rem 0.1rem;
                border-bottom: 1px solid rgba(125, 211, 252, 0.09);
            }

            [data-testid="stCheckbox"] label {
                color: var(--text);
                font-size: 0.94rem;
                font-weight: 600;
            }

            [data-testid="stCheckbox"] input {
                accent-color: var(--cyan);
            }

            .task-left {
                display: flex;
                align-items: center;
                gap: 0.72rem;
                min-width: 0;
            }

            .checkbox {
                width: 1.05rem;
                height: 1.05rem;
                display: grid;
                place-items: center;
                flex: 0 0 auto;
                border: 1px solid rgba(147, 169, 189, 0.7);
                border-radius: 6px;
                color: #031018;
                font-size: 0.72rem;
                font-weight: 900;
            }

            .checkbox.done {
                border-color: var(--green);
                background: var(--green);
            }

            .task-name {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-weight: 600;
            }

            .priority {
                flex: 0 0 auto;
                border-radius: 999px;
                padding: 0.28rem 0.58rem;
                font-size: 0.72rem;
                font-weight: 800;
            }

            .priority.high { color: #fecdd3; background: rgba(251, 113, 133, 0.12); }
            .priority.medium { color: #fde68a; background: rgba(251, 191, 36, 0.12); }
            .priority.low { color: #bae6fd; background: rgba(56, 189, 248, 0.12); }

            .progress-copy {
                display: flex;
                justify-content: space-between;
                margin: 0.85rem 0 0.35rem;
                color: var(--muted);
                font-size: 0.86rem;
                font-weight: 600;
            }

            .progress-track {
                width: 100%;
                height: 0.65rem;
                overflow: hidden;
                border-radius: 999px;
                background: rgba(125, 211, 252, 0.1);
            }

            .progress-fill {
                height: 100%;
                border-radius: inherit;
                background: linear-gradient(90deg, var(--cyan), var(--blue));
                box-shadow: 0 0 18px rgba(34, 211, 238, 0.42);
            }

            .subject-name, .calendar-time {
                color: var(--muted);
                font-weight: 700;
            }

            .subject-hours, .calendar-event {
                color: var(--text);
                font-weight: 700;
            }

            .mini-note {
                margin-top: 0.75rem;
                color: var(--soft);
                font-size: 0.82rem;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                border: 0;
            }

            div[data-testid="stMetric"] {
                padding: 0;
                background: transparent;
            }

            div[data-testid="stProgress"] > div {
                background: rgba(125, 211, 252, 0.1);
            }

            @media (max-width: 900px) {
                .block-container {
                    padding: 1.1rem 0.9rem 2rem;
                }

                .hero {
                    align-items: stretch;
                    flex-direction: column;
                    border-radius: 18px;
                }

                .status-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }

                .metric-row {
                    grid-template-columns: 1fr;
                }

                .briefing-list {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_now() -> datetime:
    """Centralize time access so it is easy to replace in tests later."""
    return datetime.now()


def get_greeting(now: datetime) -> str:
    if now.hour < 12:
        return f"Good Morning, {APP_OWNER}"
    if now.hour < 17:
        return f"Good Afternoon, {APP_OWNER}"
    return f"Good Evening, {APP_OWNER}"


def get_todays_tasks() -> list[Task]:
    """Load persistent tasks after making sure today's starter set exists."""
    today = get_now().date()
    ensure_daily_tasks(today)
    return get_tasks_for_date(today)


def get_study_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the study card's data frames from persisted study sessions."""
    today = get_now().date()
    subject_minutes = get_study_subject_breakdown(today)
    subject_breakdown = pd.DataFrame(
        [
            {"Subject": subject, "Hours": round(minutes / 60, 2)}
            for subject, minutes in subject_minutes
        ],
        columns=["Subject", "Hours"],
    )

    week_start = today - timedelta(days=today.weekday())
    minutes_by_day = get_study_minutes_between(week_start, today)
    week_dates = [week_start + timedelta(days=offset) for offset in range(7)]
    weekly_study = pd.DataFrame(
        {
            "Day": [day.strftime("%a") for day in week_dates],
            "Hours": [round(minutes_by_day.get(day, 0) / 60, 2) for day in week_dates],
        }
    )
    return subject_breakdown, weekly_study


def get_workout_data() -> pd.DataFrame:
    """Build the workout chart's data frame from saved workout sessions."""
    today = get_now().date()
    week_start = today - timedelta(days=today.weekday())
    workout_totals = get_workout_totals_between(week_start, today)
    week_dates = [week_start + timedelta(days=offset) for offset in range(7)]
    return pd.DataFrame(
        {
            "Day": [day.strftime("%a") for day in week_dates],
            "Minutes": [workout_totals.get(day, (0, 0.0))[0] for day in week_dates],
            "Distance": [workout_totals.get(day, (0, 0.0))[1] for day in week_dates],
        }
    )


def get_calendar_events() -> tuple[pd.DataFrame, str]:
    """Fetch Google Calendar events without starting OAuth during page render."""
    if not is_calendar_configured():
        return pd.DataFrame(columns=["Time", "Event"]), "Calendar setup needed"

    try:
        events = get_upcoming_events()
    except CalendarSetupError as error:
        return pd.DataFrame(columns=["Time", "Event"]), str(error)

    return (
        pd.DataFrame(
            [{"Time": event.time, "Event": event.title} for event in events],
            columns=["Time", "Event"],
        ),
        "Google Calendar synced",
    )


def card_start(title: str, icon: str) -> None:
    st.markdown(
        f"""
        <div class="card-header">
            <h2 class="card-title">{title}</h2>
            <span class="card-icon">{icon}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_end() -> None:
    """Native Streamlit containers own the boundary of every dashboard card."""


def render_progress(label: str, percent: int) -> None:
    st.markdown(
        f"""
        <div class="progress-copy">
            <span>{label}</span>
            <span>{percent}%</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width: {percent}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_tiles(metrics: list[tuple[str, str]]) -> None:
    tiles = "".join(
        f"""
        <div class="metric-tile">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """
        for label, value in metrics
    )
    st.markdown(f'<div class="metric-row">{tiles}</div>', unsafe_allow_html=True)


def render_daily_briefing(
    tasks: list[Task],
    events: pd.DataFrame,
    subject_breakdown: pd.DataFrame,
    weekly_workouts: pd.DataFrame,
) -> None:
    """Render a local, data-driven command brief for the current day."""
    briefing = build_daily_briefing(
        today=get_now().date(),
        tasks=tasks,
        calendar_events=events,
        subject_breakdown=subject_breakdown,
        weekly_workouts=weekly_workouts,
        habits=get_habits_for_date(get_now().date()),
    )
    focus_items = "".join(
        f'<div class="briefing-item">{escape(item)}</div>' for item in briefing.focus_items
    )
    st.markdown(
        f"""
        <section class="briefing-card">
            <div class="briefing-label">Daily Briefing</div>
            <div class="briefing-headline">{escape(briefing.headline)}</div>
            <p class="briefing-summary">{escape(briefing.summary)}</p>
            <div class="briefing-list">{focus_items}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


@st.fragment(run_every="60s")
def render_header() -> None:
    now = get_now()
    st.markdown(
        f"""
        <section class="hero">
            <div>
                <div class="title-row">
                    <div class="brand-mark">◈</div>
                    <div>
                        <p class="eyebrow">{get_greeting(now)}</p>
                        <h1>SHREYAS OS</h1>
                    </div>
                </div>
                <p class="subtitle">Personal Command Center</p>
            </div>
            <div class="status-grid">
                <div class="status-chip">
                    <span class="chip-label">Date</span>
                    <span class="chip-value">{now.strftime("%d %B %Y")}</span>
                </div>
                <div class="status-chip">
                    <span class="chip-label">Day</span>
                    <span class="chip-value">{now.strftime("%A")}</span>
                </div>
                <div class="status-chip">
                    <span class="chip-label">Time</span>
                    <span class="chip-value">{now.strftime("%I:%M %p")}</span>
                </div>
                <div class="status-chip">
                    <span class="chip-label">Mode</span>
                    <span class="chip-value">Focused</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_tasks_card_content(tasks: list[Task]) -> None:
    completed_count = sum(task.completed for task in tasks)
    progress_percent = round((completed_count / len(tasks)) * 100) if tasks else 0

    card_start("Today's Tasks", "[x]")
    with st.form("add-task-form", clear_on_submit=True):
        name_col, priority_col, submit_col = st.columns([3.1, 1.35, 0.8], vertical_alignment="bottom")
        with name_col:
            task_name = st.text_input("New task", placeholder="What needs doing?")
        with priority_col:
            task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        with submit_col:
            submitted = st.form_submit_button("Add")

    if submitted:
        if not task_name.strip():
            st.warning("Give the task a name first.")
        elif add_task(get_now().date(), task_name, task_priority):
            st.rerun()
        else:
            st.warning("That task is already on today's list.")

    if not tasks:
        st.markdown('<div class="mini-note">Clear board. Add one meaningful task to begin.</div>', unsafe_allow_html=True)

    for task in tasks:
        task_col, priority_col, remove_col = st.columns([4.2, 1.1, 0.9], vertical_alignment="center")
        with task_col:
            is_complete = st.checkbox(
                task.name,
                value=task.completed,
                key=f"task-{task.id}",
                help=f"Mark {task.name} as complete",
            )
            if is_complete != task.completed:
                set_task_completion(task.id, is_complete)
                st.rerun()
        with priority_col:
            st.markdown(
                f'<span class="priority {task.priority.lower()}">{task.priority}</span>',
                unsafe_allow_html=True,
            )
        with remove_col:
            if st.button("", key=f"remove-{task.id}", icon=":material/delete:", help=f"Remove {task.name}"):
                delete_task(task.id)
                st.rerun()
    render_progress("Today's Progress", progress_percent)
    card_end()


def _render_study_card_content(subject_breakdown: pd.DataFrame, weekly_study: pd.DataFrame) -> None:
    today_hours = float(subject_breakdown["Hours"].sum())
    week_hours = float(weekly_study["Hours"].sum())
    study_streak = get_study_streak(get_now().date())

    card_start("Study Statistics", "[~]")
    with st.form("log-study-form", clear_on_submit=True):
        subject_col, duration_col, submit_col = st.columns([2.2, 1.2, 0.8], vertical_alignment="bottom")
        with subject_col:
            subject = st.text_input("Subject", placeholder="Backend, Linux, College...")
        with duration_col:
            duration = st.number_input("Minutes", min_value=15, max_value=720, value=60, step=15)
        with submit_col:
            log_study = st.form_submit_button("Log session")

    if log_study:
        if not subject.strip():
            st.warning("Add a subject before logging the session.")
        else:
            add_study_session(get_now().date(), subject, int(duration))
            st.rerun()

    render_metric_tiles(
        [
            ("Study Hours Today", f"{today_hours:g}h"),
            ("This Week", f"{week_hours:g}h"),
            ("Study Streak", f"{study_streak}d"),
        ]
    )
    render_progress("Daily target", min(round(today_hours / 10 * 100), 100))

    if subject_breakdown.empty:
        st.markdown('<div class="mini-note">No study sessions logged today.</div>', unsafe_allow_html=True)
    else:
        chart = (
            alt.Chart(subject_breakdown)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Subject:N", title=None, axis=alt.Axis(labelColor="#93a9bd")),
                y=alt.Y("Hours:Q", title=None, axis=alt.Axis(labelColor="#93a9bd", gridColor="#123047")),
                color=alt.value("#22d3ee"),
                tooltip=["Subject", "Hours"],
            )
            .properties(height=190)
        )
        st.altair_chart(chart, use_container_width=True)

    rows = "".join(
        f"""
        <div class="subject-row">
            <span class="subject-name">{escape(str(row.Subject))}</span>
            <span class="subject-hours">{row.Hours:g} hrs</span>
        </div>
        """
        for row in subject_breakdown.itertuples()
    )
    if rows:
        st.markdown(rows, unsafe_allow_html=True)
    card_end()


def _render_workout_card_content(weekly_workouts: pd.DataFrame) -> None:
    workouts_completed = int((weekly_workouts["Minutes"] > 0).sum())
    total_minutes = int(weekly_workouts["Minutes"].sum())
    total_distance = float(weekly_workouts["Distance"].sum())
    today_minutes = int(weekly_workouts.loc[weekly_workouts["Day"] == get_now().strftime("%a"), "Minutes"].sum())
    workout_streak = get_workout_streak(get_now().date())

    card_start("Workout Statistics", "[>]")
    with st.form("log-workout-form", clear_on_submit=True):
        type_col, duration_col, distance_col, submit_col = st.columns(
            [1.7, 1.05, 1.05, 0.9], vertical_alignment="bottom"
        )
        with type_col:
            workout_type = st.selectbox(
                "Workout type",
                ["Strength", "Running", "Cycling", "Mobility", "Sport"],
            )
        with duration_col:
            duration = st.number_input("Minutes", min_value=10, max_value=480, value=45, step=5, key="workout-duration")
        with distance_col:
            distance = st.number_input("Distance (km)", min_value=0.0, max_value=200.0, value=0.0, step=0.5)
        with submit_col:
            log_workout = st.form_submit_button("Log workout")

    if log_workout:
        add_workout_session(get_now().date(), workout_type, int(duration), float(distance))
        st.rerun()

    render_metric_tiles(
        [
            ("Today", "Done" if today_minutes else "Pending"),
            ("Weekly Workouts", f"{workouts_completed}/5"),
            ("Run Distance", f"{total_distance:g} km"),
        ]
    )
    render_progress("Workout streak", min(workout_streak * 10, 100))
    render_progress("Weekly target", min(round(workouts_completed / 5 * 100), 100))

    chart = (
        alt.Chart(weekly_workouts)
        .mark_area(
            line={"color": "#38bdf8"},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(56, 189, 248, 0.45)", offset=0),
                    alt.GradientStop(color="rgba(56, 189, 248, 0.03)", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
        )
        .encode(
            x=alt.X("Day:N", title=None, axis=alt.Axis(labelColor="#93a9bd")),
            y=alt.Y("Minutes:Q", title=None, axis=alt.Axis(labelColor="#93a9bd", gridColor="#123047")),
            tooltip=["Day", "Minutes"],
        )
        .properties(height=190)
    )
    st.altair_chart(chart, use_container_width=True)
    st.markdown(
        f'<div class="mini-note">Training volume this week: {total_minutes} minutes | Current streak: {workout_streak} days</div>',
        unsafe_allow_html=True,
    )
    card_end()


def _render_habits_card_content() -> None:
    """Render recurring habits with independent daily completion tracking."""
    today = get_now().date()
    habits = get_habits_for_date(today)

    card_start("Habit Tracker", "[+]" )
    with st.form("add-habit-form", clear_on_submit=True):
        habit_name = st.text_input("New habit", placeholder="Read 20 minutes, drink water...")
        add_habit_button = st.form_submit_button("Add habit")

    if add_habit_button:
        if not habit_name.strip():
            st.warning("Give the habit a name first.")
        elif add_habit(habit_name):
            st.rerun()
        else:
            st.warning("That habit already exists.")

    if not habits:
        st.markdown('<div class="mini-note">Build your first repeatable habit.</div>', unsafe_allow_html=True)

    completed_count = 0
    for habit in habits:
        habit_col, streak_col, remove_col = st.columns([4.0, 1.2, 0.9], vertical_alignment="center")
        with habit_col:
            is_complete = st.checkbox(habit.name, value=habit.completed, key=f"habit-{habit.id}")
            if is_complete != habit.completed:
                set_habit_completion(habit.id, today, is_complete)
                st.rerun()
        with streak_col:
            st.markdown(
                f'<span class="priority low">{get_habit_streak(habit.id, today)}d</span>',
                unsafe_allow_html=True,
            )
        with remove_col:
            if st.button("", key=f"remove-habit-{habit.id}", icon=":material/delete:", help=f"Remove {habit.name}"):
                delete_habit(habit.id)
                st.rerun()
        completed_count += int(habit.completed)

    progress_percent = round(completed_count / len(habits) * 100) if habits else 0
    render_progress("Habit completion", progress_percent)
    card_end()


def _render_history_card_content() -> None:
    """Show a compact, read-only summary for any past or present day."""
    today = get_now().date()
    card_start("Daily History", "[<]")
    selected_date = st.date_input("Review date", value=today, max_value=today, key="history-date")
    (
        task_total,
        task_completed,
        study_minutes,
        workout_minutes,
        workout_distance,
        habit_total,
        habit_completed,
    ) = get_day_summary(selected_date)

    render_metric_tiles(
        [
            ("Tasks", f"{task_completed}/{task_total}"),
            ("Study", f"{study_minutes / 60:g}h"),
            ("Workout", f"{workout_minutes}m"),
        ]
    )
    task_progress = round(task_completed / task_total * 100) if task_total else 0
    habit_progress = round(habit_completed / habit_total * 100) if habit_total else 0
    render_progress("Task completion", task_progress)
    render_progress("Habit completion", habit_progress)
    st.markdown(
        f'<div class="mini-note">Distance logged: {workout_distance:g} km | Habits: {habit_completed}/{habit_total}</div>',
        unsafe_allow_html=True,
    )
    card_end()


def _render_calendar_card_content(events: pd.DataFrame, calendar_status: str) -> None:
    card_start("Upcoming Calendar Events", "[o]")
    if is_calendar_configured() and not is_calendar_authorized():
        if st.button("Connect Google Calendar", icon=":material/calendar_month:"):
            try:
                connect_google_calendar()
            except CalendarSetupError as error:
                st.error(str(error))
            else:
                st.rerun()

    rows = "".join(
        f"""
        <div class="calendar-row">
            <span class="calendar-time">{event.Time}</span>
            <span class="calendar-event">{escape(str(event.Event))}</span>
        </div>
        """
        for event in events.itertuples()
    )
    if rows:
        st.markdown(rows, unsafe_allow_html=True)
    else:
        st.markdown('<div class="mini-note">No upcoming events to display.</div>', unsafe_allow_html=True)

    if not is_calendar_configured():
        st.markdown(
            '<div class="mini-note">Add credentials.json to connect your primary Google Calendar.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="mini-note">{escape(calendar_status)}</div>', unsafe_allow_html=True)
    card_end()


def render_tasks_card(tasks: list[Task]) -> None:
    """Keep task controls inside one native Streamlit card."""
    with st.container(border=True):
        _render_tasks_card_content(tasks)


def render_study_card(subject_breakdown: pd.DataFrame, weekly_study: pd.DataFrame) -> None:
    """Keep study controls and data visualisation inside one native card."""
    with st.container(border=True):
        _render_study_card_content(subject_breakdown, weekly_study)


def render_workout_card(weekly_workouts: pd.DataFrame) -> None:
    """Keep workout controls and data visualisation inside one native card."""
    with st.container(border=True):
        _render_workout_card_content(weekly_workouts)


def render_habits_card() -> None:
    """Keep habit controls and streaks inside one native card."""
    with st.container(border=True):
        _render_habits_card_content()


def render_history_card() -> None:
    """Keep selected-day history summary inside one native card."""
    with st.container(border=True):
        _render_history_card_content()


def render_calendar_card(events: pd.DataFrame, calendar_status: str) -> None:
    """Keep calendar controls and events inside one native card."""
    with st.container(border=True):
        _render_calendar_card_content(events, calendar_status)


def render_dashboard() -> None:
    tasks = get_todays_tasks()
    subject_breakdown, weekly_study = get_study_data()
    weekly_workouts = get_workout_data()
    events, calendar_status = get_calendar_events()

    st.markdown('<main class="os-shell">', unsafe_allow_html=True)
    render_header()
    render_daily_briefing(tasks, events, subject_breakdown, weekly_workouts)

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        render_tasks_card(tasks)
    with right:
        render_calendar_card(events, calendar_status)

    study_col, workout_col = st.columns(2, gap="large")
    with study_col:
        render_study_card(subject_breakdown, weekly_study)
    with workout_col:
        render_workout_card(weekly_workouts)

    habit_col, history_col = st.columns(2, gap="large")
    with habit_col:
        render_habits_card()
    with history_col:
        render_history_card()

    st.markdown("</main>", unsafe_allow_html=True)


def main() -> None:
    configure_page()
    initialize_database()
    inject_css()
    render_dashboard()


if __name__ == "__main__":
    main()
