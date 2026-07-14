from pydantic import BaseModel, Field

class Decision(BaseModel):
    decision: str = Field(..., description = "A decision made during the meeting")
    context: str | None = Field(
        None, description = "Brief context or rationale behind the decision, if stated"
    )

class ActionItem(BaseModel):
    assignee: str = Field(..., description = "Person responsible for the task")
    task: str = Field(..., description = "What needs to be done")
    deadline: str | None = Field(
        None, description = "Deadline as mentioned in the meeting (e.g. 'next Friday', 'EOD Monday'). "
        "Null if no deadline was stated - do not infer one.",
    )

class AgendaStatus(BaseModel):
    agenda_item: str = Field(..., description = "The agenda item as provided")
    covered: bool = Field(..., description = "Whether this item was addressed in the meeting")
    notes: str | None = Field(
        None, description = "Optional note on how/why it was or wasn't covered"
    )

class MeetingSummary(BaseModel):
    summary: str = Field(..., description = "Concise paragraph summary of the meeting")
    decisions: list[Decision] = Field(default_factory = list)
    action_items: list[ActionItem] = Field(default_factory = list)
    agenda_status: list[AgendaStatus] = Field(default_factory = list)