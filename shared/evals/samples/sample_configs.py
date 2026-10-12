"""Stand-in configurations for the synthetic sample set (see samples/README.md).

Both return hard-coded synthetic results keyed by question text, so runs are deterministic.
"""

from evals.models import Configuration, RetrievalResult, RetrieveFn, UserProfile


def _result(document_id: str, chunk_id: str, score: float, section: str) -> RetrievalResult:
    return RetrievalResult(document_id=document_id, chunk_id=chunk_id, score=score, section=section)


_SEMANTIC: dict[str, list[RetrievalResult]] = {
    "How many days of parental leave does an employee get?": [
        _result("leave-policy-de", "leave-3", 0.82, "parental-leave"),
        _result("benefits-overview", "ben-1", 0.55, "overview"),
    ],
    "How often is a work laptop refreshed?": [
        _result("travel-policy", "trv-2", 0.61, "booking"),
        _result("it-equipment-policy", "it-4", 0.58, "laptops"),
        _result("exec-comp-policy", "exec-7", 0.41, "equity"),  # deliberately not entitled
    ],
    "Does the company sponsor pet insurance?": [
        _result("benefits-overview", "ben-9", 0.40, "insurance"),
    ],
}

_HYBRID: dict[str, list[RetrievalResult]] = {
    "How many days of parental leave does an employee get?": [
        _result("leave-policy-de", "leave-3", 0.91, "parental-leave"),
    ],
    "How often is a work laptop refreshed?": [
        _result("it-equipment-policy", "it-4", 0.88, "laptops"),
        _result("travel-policy", "trv-2", 0.52, "booking"),
    ],
    "Does the company sponsor pet insurance?": [],
}


def _retriever(table: dict[str, list[RetrievalResult]]) -> RetrieveFn:
    def retrieve(question: str, profile: UserProfile) -> list[RetrievalResult]:
        return list(table.get(question, []))

    return retrieve


semantic = Configuration(name="semantic", retrieve=_retriever(_SEMANTIC))
hybrid = Configuration(name="hybrid", retrieve=_retriever(_HYBRID))
