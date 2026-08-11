# SHREYAS OS

Personal Command Center built with Streamlit and SQLite. It is a dark, focused daily dashboard for tasks, study, workouts, and upcoming events.

## Current Features

- Live local greeting, date, day, and time
- Persistent daily tasks with completion, priority, add, and remove controls
- Study session logger with daily totals, weekly chart, subject breakdown, and streak
- Workout logger with weekly activity chart, training volume, distance, and streak
- Upcoming-event panel using sample data until calendar integration is added
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

The app calls database functions such as `add_task()` or `add_study_session()` instead of writing SQL in the UI. This separation keeps the interface easier to maintain and makes a future migration to a hosted database much simpler.

## Planned Modules

1. Replace sample calendar events with Google Calendar.
2. Add previous-day history and editable task details.
3. Add a habit tracker and dashboard streak view.
4. Add an AI daily briefing based on your real dashboard data.

## Future Integrations

- **Google Calendar API:** add OAuth credentials in `.streamlit/secrets.toml`, then replace `get_calendar_events()` with a calendar service.
- **Hosted database:** move the functions in `database.py` to Supabase, Neon, or another PostgreSQL provider when you want multi-device access.
- **AI briefing:** send a compact, structured summary of tasks, events, study, and workout data to an LLM and render the response as a morning briefing.
