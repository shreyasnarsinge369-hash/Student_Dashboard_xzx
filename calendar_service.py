"""Google Calendar integration for SHREYAS OS.

The dashboard keeps OAuth credentials local. Add a Google Desktop OAuth client
file named ``credentials.json`` to the project folder, then connect from the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
PROJECT_DIR = Path(__file__).parent
CREDENTIALS_PATH = PROJECT_DIR / "credentials.json"
TOKEN_PATH = PROJECT_DIR / "token.json"


class CalendarSetupError(RuntimeError):
    """Raised when Google Calendar cannot be read yet."""


@dataclass(frozen=True)
class CalendarEvent:
    """The concise event shape consumed by the dashboard."""

    time: str
    title: str


def is_calendar_configured() -> bool:
    """Return whether the local OAuth client file is present."""
    return CREDENTIALS_PATH.exists()


def is_calendar_authorized() -> bool:
    """Return whether a previously approved Google token is available."""
    return TOKEN_PATH.exists()


def _get_credentials(allow_interactive: bool):
    """Load, refresh, or request Google OAuth credentials."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as error:
        raise CalendarSetupError(
            "Google Calendar packages are missing. Install requirements.txt and restart the app."
        ) from error

    if not CREDENTIALS_PATH.exists():
        raise CalendarSetupError("Add credentials.json before connecting Google Calendar.")

    credentials = None
    if TOKEN_PATH.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid:
        if not allow_interactive:
            raise CalendarSetupError("Click Connect Google Calendar to authorize this dashboard.")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        credentials = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def connect_google_calendar() -> None:
    """Open the one-time OAuth flow and save a local refresh token."""
    _get_credentials(allow_interactive=True)


def get_upcoming_events(max_results: int = 5) -> list[CalendarEvent]:
    """Read the next upcoming events from the user's primary calendar."""
    try:
        from googleapiclient.discovery import build
    except ImportError as error:
        raise CalendarSetupError(
            "Google Calendar packages are missing. Install requirements.txt and restart the app."
        ) from error

    service = build("calendar", "v3", credentials=_get_credentials(allow_interactive=False))
    events = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=datetime.now().astimezone().isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )

    dashboard_events = []
    for event in events:
        start = event.get("start", {})
        start_value = start.get("dateTime")
        if start_value:
            event_time = datetime.fromisoformat(start_value.replace("Z", "+00:00")).astimezone()
            time_label = event_time.strftime("%H:%M")
        else:
            time_label = "All day"
        dashboard_events.append(CalendarEvent(time_label, event.get("summary", "Untitled event")))

    return dashboard_events
