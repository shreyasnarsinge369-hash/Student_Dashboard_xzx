# SHREYAS OS

Personal Command Center built with Streamlit and SQLite. It is a dark, focused daily dashboard for tasks, study, workouts, and upcoming events.

## Current Features

- Live local greeting, date, day, and time
- Persistent daily tasks with completion, priority, add, and remove controls
- Study session logger with daily totals, weekly chart, subject breakdown, and streak
- Workout logger with weekly activity chart, training volume, distance, and streak
- Google Calendar panel that reads upcoming events from your primary calendar
- Habit tracker with daily completion and individual streaks
- Daily history view for reviewing task, study, workout, and habit performance
- Local SQLite storage with no external APIs or accounts required

## Project Structure

```text
Daily Dashboard/
|- app.py                 # Streamlit UI, charts, and page styling
|- database.py            # SQLite schema and data-access functions
|- requirements.txt       # Python dependencies
|- .streamlit/config.toml # Streamlit theme and local server settings
|- shreyas_os.db          # Created locally at runtime; intentionally ignored by Git
```

## Run Locally

1. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Start the dashboard:

   ```powershell
   python -m streamlit run app.py
   ```

3. Open `http://127.0.0.1:8501`.

## How the Data Layer Works

`database.py` uses Python's built-in `sqlite3` module. The first dashboard run creates three tables:

- `tasks`: daily tasks, priority, and completion state
- `study_sessions`: subject and duration for each study session
- `workout_sessions`: workout type, duration, distance, and date
- `habits`: reusable habit definitions
- `habit_completions`: per-day completion state for each habit

The app calls database functions such as `add_task()` or `add_study_session()` instead of writing SQL in the UI. This separation keeps the interface easier to maintain and makes a future migration to a hosted database much simpler.

## Connect Google Calendar

The Calendar panel is ready for a personal Google account. It uses read-only OAuth, and credentials are intentionally excluded from Git.

1. In Google Cloud Console, create a project and enable the Google Calendar API.
2. Create an OAuth 2.0 Client ID with the **Desktop app** application type.
3. Download the JSON client file and rename it to `credentials.json`.
4. Place `credentials.json` in this project folder beside `app.py`.
5. Restart Streamlit and select **Connect Google Calendar** in the Calendar card.
6. Complete Google's one-time consent flow. A local `token.json` is created automatically and remains ignored by Git.

The dashboard requests only the `calendar.readonly` scope and reads the next five events from your primary calendar. Both `credentials.json` and `token.json` must remain private.

## Planned Modules

1. Add an AI daily briefing based on your real dashboard data.
2. Add task details, due times, and a richer past-day review.
3. Move the local SQLite layer to a hosted database for multi-device access.

## Future Integrations

- **Google Calendar API:** add OAuth credentials in `.streamlit/secrets.toml`, then replace `get_calendar_events()` with a calendar service.
- **Hosted database:** move the functions in `database.py` to Supabase, Neon, or another PostgreSQL provider when you want multi-device access.
- **AI briefing:** send a compact, structured summary of tasks, events, study, and workout data to an LLM and render the response as a morning briefing.
