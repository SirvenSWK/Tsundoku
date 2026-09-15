from __future__ import annotations

import os
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from tsundoku.models.tasks import Ingestion, Task

from dotenv import load_dotenv

from tsundoku.models import settings

import json

currentDateTime = datetime.now().astimezone()
load_dotenv()
apiKey = settings.loadApi()


class TaskDraft(BaseModel):
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
    tasks: list[TaskDraft] = Field(default_factory=list)
    message: str | None = None


systemPrompt = f"""Extract actionable tasks from the user's message.

Reference time: {currentDateTime.isoformat()}

Rules:
- Actionable input → return one or more tasks.
- No actionable intent or insufficient information → return tasks=[] and a brief helpful message.
- Never invent tasks.
- Preserve unknown fields as null or sensible defaults.
- Resolve relative dates using the reference time.
- deadline: ISO 8601 datetime or null.
- durationMinutes: realistic estimate, usually 45–120, or null.
- priority: low, normal, or high.
"""


def fallbackOrganize(rawText: str) -> OrganizeResult:
    apiKey = settings.loadApi()
    return OrganizeResult(
        tasks=[
            TaskDraft(
                title=rawText[:200],
                description=rawText if len(rawText) > 200 else "",
            )
        ]
    )


def organizeWithLlm(rawText: str) -> OrganizeResult:

    if not apiKey:
        return OrganizeResult(
            task=[],
            message="Add your Groq API key from https://console.groq.com/keys in settings to use AI organization"
        )

    from groq import Groq

    client = Groq(api_key = apiKey)
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system","content": systemPrompt},
                {"role": "user", "content": rawText},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "organize_result",
                    "schema": OrganizeResult.model_json_schema(),
                },
            },
        )
    except:
        return OrganizeResult(
            task=[],
            messgae="There was a problem connecting to Groq. Check your API key and try again."
        )

    content = completion.choices[0].message.content

    if not content:
        return fallbackOrganize(rawText)

    result = OrganizeResult.model_validate(json.loads(content))

    return result


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
