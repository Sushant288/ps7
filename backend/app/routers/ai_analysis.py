"""AI analysis endpoints — streaming SSE responses backed by Gemini."""
import json
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import SiteReadinessScore
from app.services.ai_service import (
    stream_site_analysis,
    stream_site_comparison,
    stream_site_query,
)
from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
    site: SiteReadinessScore
    use_case: str = "retail"


class CompareRequest(BaseModel):
    sites: list[SiteReadinessScore]
    use_case: str = "retail"


class QueryRequest(BaseModel):
    question: str
    site: SiteReadinessScore
    use_case: str = "retail"


def _sse(text_gen):
    try:
        for chunk in text_gen:
            yield f"data: {json.dumps({'text': chunk})}\n\n"
    except RuntimeError as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}


@router.post("/analyze")
async def ai_analyze_site(req: AnalyzeRequest, x_gemini_key: Optional[str] = Header(default=None)):
    if not x_gemini_key and not settings.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API key required. Enter it in the UI or set it in backend .env.")
    try:
        return StreamingResponse(_sse(stream_site_analysis(req.site, req.use_case, x_gemini_key)),
                                 media_type="text/event-stream", headers=SSE_HEADERS)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def ai_compare_sites(req: CompareRequest, x_gemini_key: Optional[str] = Header(default=None)):
    if not x_gemini_key and not settings.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API key required. Enter it in the UI or set it in backend .env.")
    if len(req.sites) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 sites to compare")
    try:
        return StreamingResponse(_sse(stream_site_comparison(req.sites, req.use_case, x_gemini_key)),
                                 media_type="text/event-stream", headers=SSE_HEADERS)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def ai_query_site(req: QueryRequest, x_gemini_key: Optional[str] = Header(default=None)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if not x_gemini_key and not settings.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API key required. Enter it in the UI or set it in backend .env.")
    try:
        return StreamingResponse(_sse(stream_site_query(req.question, req.site, req.use_case, x_gemini_key)),
                                 media_type="text/event-stream", headers=SSE_HEADERS)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
