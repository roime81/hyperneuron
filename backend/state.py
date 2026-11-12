from typing import Annotated, List, Optional, TypedDict
from pydantic import BaseModel, Field
import operator

class ResearchPlan(BaseModel):
    domain: str = Field(description="e.g., Corporate Intelligence, Legal/Financial Due Diligence, or General")
    needs_clarification: bool = Field(default=False)
    clarification_question: Optional[str] = Field(default=None)
    thinking_brief: str = Field(description="Specific analytical angle for Deep Thinking")
    citation_queries: List[str] = Field(description="Targeted search queries for Deep Citation")
    quant_brief: str = Field(description="Specific metrics or tables for Quantified Researcher")

class SpecialistReport(BaseModel):
    agent_name: str
    model_used: str
    summary: str
    key_findings: List[str]
    citations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)

class HyperneuronState(TypedDict):
    user_prompt: str
    plan: Optional[dict]
    specialist_reports: Annotated[List[dict], operator.add]
    iteration: int
    final_report: Optional[str]
