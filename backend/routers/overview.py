import uuid
import asyncio
from fastapi import APIRouter, BackgroundTasks, Query
from schemas.overview import FigureResponse, TopicAnalysisStart, TopicAnalysisStatus
from services.overview_service import get_user_growth_figure, get_messages_over_time_figure

router = APIRouter(prefix="/api/overview", tags=["overview"])

# In-memory job store (single-worker only — sufficient for internal dashboard)
_jobs: dict[str, TopicAnalysisStatus] = {}


@router.get("/user-growth", response_model=FigureResponse)
async def user_growth(segment: str = Query("release")):
    return FigureResponse(figure=await get_user_growth_figure(segment))


@router.get("/messages-over-time", response_model=FigureResponse)
async def messages_over_time(segment: str = Query("release")):
    return FigureResponse(figure=await get_messages_over_time_figure(segment))


@router.post("/topic-analysis/start", response_model=TopicAnalysisStart)
async def start_topic_analysis(
    background_tasks: BackgroundTasks,
    segment: str = Query("release"),
):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = TopicAnalysisStatus(status="running")
    background_tasks.add_task(_run_topic_analysis, job_id, segment)
    return TopicAnalysisStart(job_id=job_id)


@router.get("/topic-analysis/status/{job_id}", response_model=TopicAnalysisStatus)
async def topic_analysis_status(job_id: str):
    return _jobs.get(job_id, TopicAnalysisStatus(status="error"))


async def _run_topic_analysis(job_id: str, segment: str) -> None:
    try:
        from services.ai_service import analyze_topics
        results = await analyze_topics(segment)
        _jobs[job_id] = TopicAnalysisStatus(status="done", results=results)
    except Exception as exc:
        _jobs[job_id] = TopicAnalysisStatus(status="error", results={"error": str(exc)})
