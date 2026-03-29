from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import ScoreRequest, SiteReadinessScore, SiteComparison
from app.services.scoring import compute_site_score

router = APIRouter(prefix="/api/score", tags=["scoring"])


@router.post("/site", response_model=SiteReadinessScore)
async def score_site(req: ScoreRequest):
    try:
        return compute_site_score(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=SiteComparison)
async def compare_sites(requests: List[ScoreRequest]):
    if len(requests) < 2:
        raise HTTPException(
            status_code=400, detail="Need at least 2 sites to compare"
        )
    if len(requests) > 10:
        raise HTTPException(
            status_code=400, detail="Maximum 10 sites for comparison"
        )

    try:
        scores = [compute_site_score(req) for req in requests]
        ranking = sorted(
            range(len(scores)),
            key=lambda i: scores[i].composite_score,
            reverse=True,
        )

        best = scores[ranking[0]]
        recommendation = (
            f"Site {ranking[0] + 1} at ({best.lat:.4f}, {best.lng:.4f}) is recommended "
            f"with score {best.composite_score}/100 (Grade: {best.grade}). "
            f"It leads across {sum(1 for b in best.breakdowns if b.score >= 60)} of 5 layers."
        )

        return SiteComparison(sites=scores, ranking=ranking, recommendation=recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
