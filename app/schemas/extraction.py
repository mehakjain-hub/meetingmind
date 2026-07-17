from pydantic import BaseModel, Field
from enum import Enum

class Decision(BaseModel):
    decision: str = Field(..., description = "A decision made during the meeting")
    context: str | None = Field(
        None, description = "Brief context or rationale behind the decision, if stated"
    )

class ActionItem(BaseModel):
    task: str = Field(..., description="What needs to be done")
    assignee: str | None = Field(
        None, description = "Person responsible for the task. Null if no assignee was explicitly stated - do not infer one."
    )
    deadline: str | None = Field(
        None, description = "Deadline as mentioned in the meeting (e.g. 'next Friday', 'EOD Monday'). "
        "Null if no deadline was stated - do not infer one.",
    )

class AgendaItemStatus(str, Enum):
    COVERED = "covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_COVERED = "not_covered"

class AgendaItemResult(BaseModel):
    agenda_item: str = Field(..., description="The original agenda item text")
    status: AgendaItemStatus
    evidence: str = Field(
        default="",
        description="Short quote or paraphrase from transcript supporting the status. Empty if not_covered."
    )

class MeetingSummary(BaseModel):
    summary: str = Field(..., description="Concise paragraph summary of the meeting")
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    agenda_status: list[AgendaItemResult] = Field(default_factory=list)