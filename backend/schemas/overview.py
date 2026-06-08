from pydantic import BaseModel


class FigureResponse(BaseModel):
    figure: str  # JSON-encoded Plotly figure


class TopicAnalysisStart(BaseModel):
    job_id: str


class TopicAnalysisStatus(BaseModel):
    status: str  # "running" | "done" | "error"
    results: dict[str, str] | None = None
