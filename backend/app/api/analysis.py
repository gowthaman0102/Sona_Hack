from fastapi import APIRouter

from app.models.query_analysis import (
    AnalyzeRequest,
    QueryAnalysis,
)
from app.services.query_analyzer import QueryAnalyzer


router = APIRouter(
    prefix="/analysis",
    tags=["Query Analysis"],
)

query_analyzer = QueryAnalyzer()


@router.post(
    "",
    response_model=QueryAnalysis,
)
def analyze_query(
    request: AnalyzeRequest,
):
    return query_analyzer.analyze(
        request.prompt
    )
