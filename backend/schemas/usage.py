from pydantic import BaseModel


class FigureResponse(BaseModel):
    figure: str  # JSON-encoded Plotly figure
