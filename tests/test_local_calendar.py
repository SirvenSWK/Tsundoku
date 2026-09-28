import tempfile
import unittest
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from unittest.mock import MagicMock

from tsundoku.models.storage_paths import migrate_legacy_file
from tsundoku.models.tasks import Event, Task
from tsundoku.tools import googleCalendar, organizer
from tsundoku.tools.taskManager import TaskManager


class LocalDataTests(unittest.TestCase):
    def test_migration_copies_once_and_preserves_newer_data(self):
        with tempfile.TemporaryDirectory() as directory:
            oldPath = Path(directory) / "old.json"
            newPath = Path(directory) / "appdata" / "new.json"
            oldPath.write_text("old", encoding="utf-8")
            migrate_legacy_file(oldPath, newPath)
            self.assertEqual(newPath.read_text(encoding="utf-8"), "old")
            newPath.write_text("new", encoding="utf-8")
            migrate_legacy_file(oldPath, newPath)
            self.assertEqual(newPath.read_text(encoding="utf-8"), "new")

    def test_task_and_event_sync_ids_round_trip_and_adds_are_idempotent(self):
        taskManager = TaskManager()
        taskId = uuid4()
        eventId = uuid4()
        task = Task(
            id=taskId,
            title="Prepare slides",
            description="",
            scheduledStart=datetime(2026, 10, 1, 10, tzinfo=timezone.utc),
            deadline=None,
            duration=timedelta(minutes=45),
            priority="normal",
            completed=False,
            eventID=eventId,
            googleEventID="taskgoogleid",
            googleCalendarID="primary",
        )
        event = Event(
            id=eventId,
            title="Presentation",
            description="",
            scheduledStart=datetime(2026, 10, 2, 12, tzinfo=timezone.utc),
            isAllDay=False,
            googleEventID="eventgoogleid",
            googleCalendarID="primary",
        )
        taskManager.addTask(task)
        taskManager.addTask(task)
        taskManager.addEvent(event)
        taskManager.addEvent(event)

        with tempfile.TemporaryDirectory() as directory:
            with patch("tsundoku.tools.taskManager.tasksFile", Path(directory) / "tasks.json"):
                taskManager.save()
                loaded = TaskManager()
                loaded.load()

        self.assertEqual(len(loaded.tasks), 1)
        self.assertEqual(len(loaded.events), 1)
        self.assertEqual(loaded.tasks[0].eventID, eventId)
        self.assertEqual(loaded.tasks[0].googleEventID, "taskgoogleid")
        self.assertEqual(loaded.events[0].googleEventID, "eventgoogleid")


class OrganizerTests(unittest.TestCase):
    def test_event_and_task_relationships_are_assigned_locally(self):
        result = organizer.OrganizeResult(
            events=[organizer.EventDraft(title="Physics exam")],
            tasks=[organizer.TaskDraft(title="Review notes", eventRef="Physics exam")],
        )
        _, events, tasks = organizer.applyOrganizeResult(result, "Physics exam next week; review notes")
        self.assertEqual(tasks[0].eventID, events[0].id)


class GoogleCalendarMappingTests(unittest.TestCase):
    def test_login_uses_app_config_and_opens_the_system_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            clientFile = Path(directory) / "desktop-client.json"
            clientFile.write_text('{"installed": {}}', encoding="utf-8")
            with (
                patch.dict(os.environ, {"GOOGLE_OAUTH_CLIENT_FILE": str(clientFile)}),
                patch.object(googleCalendar, "InstalledAppFlow") as flowClass,
                patch.object(googleCalendar, "_write_credentials"),
                patch.object(googleCalendar, "build"),
                patch.object(googleCalendar, "_ensure_tsundoku_calendar", return_value="tsundoku-id"),
                patch.object(googleCalendar, "_save_target_calendar_id"),
                patch.object(googleCalendar, "import_calendars", return_value=3),
                patch("tsundoku.tools.taskManager.taskManager.save"),
            ):
                flowClass.from_client_secrets_file.return_value.run_local_server.return_value = object()
                googleCalendar.connect()

        flowClass.from_client_secrets_file.assert_called_once_with(
            str(clientFile), googleCalendar.SCOPES
        )
        flowClass.from_client_secrets_file.return_value.run_local_server.assert_called_once_with(
            port=0, open_browser=True
        )

    def test_all_day_item_uses_exclusive_end_date(self):
        event = Event(
            id=uuid4(),
            title="Exam",
            description="",
            scheduledStart=datetime(2026, 10, 3, tzinfo=timezone.utc),
            isAllDay=True,
        )
        body = googleCalendar._google_event_body(event)
        self.assertEqual(body["start"], {"date": "2026-10-03"})
        self.assertEqual(body["end"], {"date": "2026-10-04"})

    def test_timed_task_uses_saved_duration_and_timezone(self):
        task = Task(
            id=uuid4(),
            title="Study",
            description="",
            scheduledStart=datetime(2026, 10, 3, 10, tzinfo=timezone(timedelta(hours=2))),
            deadline=None,
            duration=timedelta(minutes=45),
            priority="normal",
            completed=False,
        )
        body = googleCalendar._google_event_body(task)
        self.assertEqual(body["start"]["dateTime"], "2026-10-03T10:00:00+02:00")
        self.assertEqual(body["end"]["dateTime"], "2026-10-03T10:45:00+02:00")

    def test_undated_item_is_not_exported(self):
        task = Task(
            id=uuid4(), title="Unscheduled", description="", scheduledStart=None,
            deadline=None, duration=None, priority="normal", completed=False,
        )
        with self.assertRaises(googleCalendar.GoogleCalendarError):
            googleCalendar._google_event_body(task)

    def test_sync_creates_an_idempotently_identified_calendar_event(self):
        task = Task(
            id=uuid4(), title="Study", description="", scheduledStart=datetime.now(timezone.utc),
            deadline=None, duration=timedelta(minutes=30), priority="normal", completed=False,
        )
        service = MagicMock()
        service.events.return_value.insert.return_value.execute.return_value = {
            "id": task.id.hex,
        }
        with (
            patch.object(googleCalendar, "_get_credentials", return_value=object()),
            patch.object(googleCalendar, "build", return_value=service),
            patch.object(googleCalendar, "target_calendar_id", return_value=None),
        ):
            googleCalendar.sync_task(task)

        self.assertEqual(task.googleEventID, task.id.hex)
        self.assertEqual(task.googleCalendarID, "primary")
        insertCall = service.events.return_value.insert.call_args.kwargs
        self.assertEqual(insertCall["calendarId"], "primary")
        self.assertEqual(insertCall["body"]["id"], task.id.hex)

    def test_sync_updates_an_existing_google_event(self):
        task = Task(
            id=uuid4(), title="Study", description="", scheduledStart=datetime.now(timezone.utc),
            deadline=None, duration=None, priority="normal", completed=False,
            googleEventID="existing-google-id",
        )
        service = MagicMock()
        with (
            patch.object(googleCalendar, "_get_credentials", return_value=object()),
            patch.object(googleCalendar, "build", return_value=service),
        ):
            googleCalendar.sync_task(task)

        service.events.return_value.update.assert_called_once()
        self.assertEqual(task.googleEventID, "existing-google-id")


if __name__ == "__main__":
    unittest.main()
