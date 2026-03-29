from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ScoreRequest
from app.services.scoring import compute_site_score
import json
import io
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/json")
async def export_json(req: ScoreRequest):
    try:
        result = compute_site_score(req)
        # Convert to dict with all nested models serialized
        content = json.dumps(result.dict(), indent=2, default=str)
        filename = f"site_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/csv")
async def export_csv(requests: List[ScoreRequest]):
    try:
        results = [compute_site_score(req) for req in requests]
        rows = [
            "lat,lng,use_case,composite_score,grade,"
            "demographic,transportation,poi,land_use,environmental,h3_index"
        ]
        for req, r in zip(requests, results):
            scores = {b.layer_name: b.score for b in r.breakdowns}
            rows.append(
                f"{r.lat},{r.lng},{req.use_case},{r.composite_score},{r.grade},"
                f"{scores.get('demographic', '')},"
                f"{scores.get('transportation', '')},"
                f"{scores.get('poi', '')},"
                f"{scores.get('land_use', '')},"
                f"{scores.get('environmental', '')},"
                f"{r.h3_index}"
            )

        content = "\n".join(rows)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=site_comparison.csv"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
