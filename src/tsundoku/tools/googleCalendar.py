from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import TypeAlias
from uuid import NAMESPACE_URL, uuid5

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tsundoku.models.storage_paths import data_directory
from tsundoku.models.tasks import Event, Task


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.app.created",
]
TOKEN_FILE = data_directory() / "google_calendar_token.json"
CLIENT_FILE = data_directory() / "google_calendar_client.json"
STATE_FILE = data_directory() / "google_calendar_state.json"
BUNDLED_CLIENT_FILE = (
    Path(__file__).resolve().parent.parent / "Data" / "google_oauth_client.json"
)
DEFAULT_CALENDAR_ID = "primary"
TSUNDOKU_CALENDAR_NAME = "Tsundoku"
DEFAULT_DURATION = timedelta(minutes=60)
CalendarItem: TypeAlias = Task | Event


class GoogleCalendarError(Exception):
    """A user-displayable Google Calendar connection or sync error."""


def _write_credentials(credentials: Credentials) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporaryPath = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=TOKEN_FILE.parent,
            prefix="google-token.", suffix=".tmp", delete=False,
        ) as file:
            temporaryPath = Path(file.name)
            file.write(credentials.to_json())
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporaryPath, TOKEN_FILE)
    finally:
        if temporaryPath is not None and temporaryPath.exists():
            temporaryPath.unlink()


def has_client_credentials() -> bool:
    return _client_credentials_file() is not None


def _client_credentials_file() -> Path | None:
    configuredPath = os.getenv("GOOGLE_OAUTH_CLIENT_FILE")
    for candidate in (
        Path(configuredPath) if configuredPath else None,
        BUNDLED_CLIENT_FILE,
        CLIENT_FILE,
    ):
        if candidate is not None and candidate.is_file():
            return candidate
    return None


def connect() -> int:
    """Authorize this desktop app directly through Google's system browser."""
    try:
        clientFile = _client_credentials_file()
        if clientFile is None:
            raise GoogleCalendarError(
                "Google sign-in isn't configured for this Tsundoku build yet. "
                "The app maintainer needs to configure its Desktop OAuth client first."
            )

        with clientFile.open(encoding="utf-8") as file:
            config = json.load(file)
        if "installed" not in config:
            raise GoogleCalendarError(
                "Tsundoku's Google OAuth setup is invalid. Please contact the app maintainer."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(clientFile), SCOPES)
        try:
            credentials = flow.run_local_server(port=0, open_browser=True)
        except Exception as error:
            if getattr(error, "error", None) == "access_denied":
                raise GoogleCalendarError(
                    "Google denied access to Tsundoku. In Google Cloud Console, open "
                    "Google Auth Platform → Audience and add this Google account under "
                    "Test users. If the app is set to Internal, sign in with an account "
                    "from that Workspace organization. Then try again."
                ) from error
            raise
        _write_credentials(credentials)
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        tsundokuCalendarID = _ensure_tsundoku_calendar(service)
        _save_target_calendar_id(tsundokuCalendarID)
        imported = import_calendars(service, tsundokuCalendarID)
        from tsundoku.tools.taskManager import taskManager
        taskManager.save()
        return imported
    except GoogleCalendarError:
        raise
    except Exception as error:
        raise GoogleCalendarError(f"Google Calendar connection failed: {error}") from error


def disconnect() -> None:
    TOKEN_FILE.unlink(missing_ok=True)


def is_connected() -> bool:
    return TOKEN_FILE.is_file()


def _get_credentials() -> Credentials:
    if not TOKEN_FILE.is_file():
        raise GoogleCalendarError("Connect Google Calendar in Settings first.")
    try:
        credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE))
        granted = set(credentials.scopes or [])
        if not set(SCOPES).issubset(granted):
            raise GoogleCalendarError(
                "Google Calendar access needs updating. Select Connect again and approve the requested access."
            )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            _write_credentials(credentials)
        if not credentials.valid:
            raise GoogleCalendarError("Google authorization expired. Reconnect in Settings.")
        return credentials
    except GoogleCalendarError:
        raise
    except Exception as error:
        raise GoogleCalendarError(
            f"Couldn't refresh Google authorization. Reconnect in Settings. ({error})"
        ) from error


def _google_event_body(item: CalendarItem) -> dict:
    if item.scheduledStart is None:
        raise GoogleCalendarError("Add a date or start time before exporting this item.")

    start = item.scheduledStart
    body = {"summary": item.title, "description": item.description or ""}
    if item.isAllDay:
        startDate = start.date()
        body["start"] = {"date": startDate.isoformat()}
        body["end"] = {"date": (startDate + timedelta(days=1)).isoformat()}
    else:
        if start.tzinfo is None:
            start = start.astimezone()
        duration = item.duration if isinstance(item, Task) else DEFAULT_DURATION
        end = start + (duration or DEFAULT_DURATION)
        body["start"] = {"dateTime": start.isoformat()}
        body["end"] = {"dateTime": end.isoformat()}
    return body


def _sync(item: CalendarItem) -> str:
    credentials = _get_credentials()
    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    calendarId = item.googleCalendarID or target_calendar_id() or DEFAULT_CALENDAR_ID
    body = _google_event_body(item)
    stableGoogleId = item.id.hex

    try:
        if item.googleEventID:
            try:
                service.events().update(
                    calendarId=calendarId,
                    eventId=item.googleEventID,
                    body=body,
                ).execute()
                return item.googleEventID
            except HttpError as error:
                if error.resp.status != 404:
                    raise

        body["id"] = stableGoogleId
        try:
            created = service.events().insert(calendarId=calendarId, body=body).execute()
            return created["id"]
        except HttpError as error:
            if error.resp.status != 409:
                raise
            service.events().update(
                calendarId=calendarId, eventId=stableGoogleId, body=body
            ).execute()
            return stableGoogleId
    except GoogleCalendarError:
        raise
    except Exception as error:
        raise GoogleCalendarError(f"Google Calendar export failed: {error}") from error


def sync_task(task: Task) -> None:
    task.googleEventID = _sync(task)
    task.googleCalendarID = task.googleCalendarID or target_calendar_id() or DEFAULT_CALENDAR_ID


def sync_event(event: Event) -> None:
    event.googleEventID = _sync(event)
    event.googleCalendarID = event.googleCalendarID or target_calendar_id() or DEFAULT_CALENDAR_ID


def _read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_target_calendar_id(calendar_id: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"targetCalendarID": calendar_id}), encoding="utf-8")


def target_calendar_id() -> str | None:
    value = _read_state().get("targetCalendarID")
    return value if isinstance(value, str) and value else None


def _ensure_tsundoku_calendar(service) -> str:
    existing = target_calendar_id()
    if existing:
        return existing
    pageToken = None
    while True:
        result = service.calendarList().list(pageToken=pageToken).execute()
        for calendar in result.get("items", []):
            if calendar.get("summary") == TSUNDOKU_CALENDAR_NAME:
                _save_target_calendar_id(calendar["id"])
                return calendar["id"]
        pageToken = result.get("nextPageToken")
        if not pageToken:
            break
    created = service.calendars().insert(body={"summary": TSUNDOKU_CALENDAR_NAME}).execute()
    return created["id"]


def _event_start(event: dict) -> tuple[datetime | None, bool]:
    start = event.get("start", {})
    if start.get("dateTime"):
        value = start["dateTime"].replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(), False
    if start.get("date"):
        return datetime.combine(date.fromisoformat(start["date"]), time.min), True
    return None, False


def import_calendars(service, tsundokuCalendarID: str) -> int:
    """Import visible calendar events locally, deduplicating by Google source IDs."""
    from tsundoku.tools.taskManager import taskManager

    known = {
        (event.sourceGoogleCalendarID, event.sourceGoogleEventID)
        for event in taskManager.getEvents()
        if event.sourceGoogleCalendarID and event.sourceGoogleEventID
    }
    pageToken = None
    imported = 0
    while True:
        calendars = service.calendarList().list(pageToken=pageToken).execute()
        for calendar in calendars.get("items", []):
            calendarID = calendar.get("id")
            if not calendarID or calendarID == tsundokuCalendarID or calendar.get("accessRole") == "freeBusyReader":
                continue
            eventPageToken = None
            while True:
                response = service.events().list(
                    calendarId=calendarID,
                    singleEvents=True,
                    showDeleted=False,
                    maxResults=2500,
                    pageToken=eventPageToken,
                ).execute()
                for googleEvent in response.get("items", []):
                    sourceID = googleEvent.get("id")
                    if not sourceID or googleEvent.get("status") == "cancelled":
                        continue
                    key = (calendarID, sourceID)
                    if key in known:
                        continue
                    start, allDay = _event_start(googleEvent)
                    if start is None:
                        continue
                    recordKey = f"{calendarID}/{sourceID}"
                    event = Event(
                        id=uuid5(NAMESPACE_URL, recordKey),
                        title=googleEvent.get("summary") or "(Untitled event)",
                        description=googleEvent.get("description") or "",
                        scheduledStart=start,
                        isAllDay=allDay,
                        sourceGoogleEventID=sourceID,
                        sourceGoogleCalendarID=calendarID,
                    )
                    taskManager.addEvent(event)
                    known.add(key)
                    imported += 1
                eventPageToken = response.get("nextPageToken")
                if not eventPageToken:
                    break
            eventPageToken = None
        pageToken = calendars.get("nextPageToken")
        if not pageToken:
            break
    return imported
