"""
Turn one natural-language dump into structured tasks (LLM-backed later).

Flow:
  raw text → OrganizeResult (Pydantic) → Task + Ingestion rows in TaskManager
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from tsundoku.models.tasks import Ingestion, Task


class TaskDraft(BaseModel):
    """One unit of work the scheduler can place on the calendar."""

    title: str
    description: str = ""
    deadline: datetime | None = None
    durationMinutes: int | None = Field(default=None, ge=1)
    priority: str = "normal"
    parentRef: str | None = Field(
        default=None,
        description="Title of parent goal when this row is a session/subtask.",
    )


class OrganizeResult(BaseModel):
    tasks: list[TaskDraft] = Field(min_length=1)


organizeSystem = """You extract actionable tasks from the user's message.
Return JSON matching the schema. Rules:
- One user message may yield several tasks (comma lists, 'and', multiple deadlines).
- Use parentRef on session rows when breaking study/prep into chunks; parent row has parentRef null.
- durationMinutes: realistic focus blocks (e.g. 45–120), null if unknown.
- priority: low | normal | high
- deadline: ISO 8601 datetime when implied, else null.
"""


def fallbackOrganize(rawText: str) -> OrganizeResult:
    """No API key: keep UX working until LLM is wired."""
    return OrganizeResult(
        tasks=[
            TaskDraft(
                title=rawText[:200],
                description=rawText if len(rawText) > 200 else "",
            )
        ]
    )


def organizeWithLlm(rawText: str) -> OrganizeResult:
    """
    Call your LLM with structured output when OPENAI_API_KEY is configured.
    """
    apiKey = os.getenv("OPENAI_API_KEY")
    if not apiKey:
        return fallbackOrganize(rawText)

    # Example shape once `openai` is installed:
    # from openai import OpenAI
    # client = OpenAI(apiKey=apiKey)
    # completion = client.beta.chat.completions.parse(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": organizeSystem},
    #         {"role": "user", "content": rawText},
    #     ],
    #     response_format=OrganizeResult,
    # )
    # return completion.choices[0].message.parsed
    return fallbackOrganize(rawText)


def applyOrganizeResult(
    result: OrganizeResult,
    rawText: str,
    ingestionID: UUID | None = None,
) -> tuple[Ingestion, list[Task]]:
    """Map LLM output to domain objects with stable IDs and parent links."""
    ingestion = Ingestion(
        id=ingestionID or uuid4(),
        rawText=rawText,
        timeStamp=datetime.now().astimezone(),
    )
    titleToId: dict[str, UUID] = {}
    built: list[Task] = []

    for draft in result.tasks:
        taskId = uuid4()
        titleToId[draft.title] = taskId
        duration = (
            timedelta(minutes=draft.durationMinutes)
            if draft.durationMinutes is not None
            else None
        )
        built.append(
            Task(
                id=taskId,
                title=draft.title,
                description=draft.description,
                deadline=draft.deadline,
                duration=duration,
                priority=draft.priority,
                completed=False,
                ingestionID=ingestion.id,
                parentID=None,
            )
        )

    for draft, task in zip(result.tasks, built, strict=True):
        if not draft.parentRef:
            continue
        parentId = titleToId.get(draft.parentRef)
        if parentId is not None:
            task.parentID = parentId

    return ingestion, built
