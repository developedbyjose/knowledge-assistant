from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCaseResult:
    question: str
    expected_filename: str
    expected_page_number: int | None
    retrieved: list[dict[str, object]]

    @property
    def top_1_passed(self) -> bool:
        return _matches_expected(
            self.retrieved[:1],
            expected_filename=self.expected_filename,
            expected_page_number=self.expected_page_number,
        )

    def top_k_passed(self, *, k: int) -> bool:
        return _matches_expected(
            self.retrieved[:k],
            expected_filename=self.expected_filename,
            expected_page_number=self.expected_page_number,
        )


def top_1_accuracy(results: list[EvaluationCaseResult]) -> float:
    if not results:
        return 0.0
    return sum(result.top_1_passed for result in results) / len(results)


def top_k_hit_rate(results: list[EvaluationCaseResult], *, k: int) -> float:
    if not results:
        return 0.0
    return sum(result.top_k_passed(k=k) for result in results) / len(results)


def _matches_expected(
    retrieved: list[dict[str, object]],
    *,
    expected_filename: str,
    expected_page_number: int | None,
) -> bool:
    for item in retrieved:
        if item.get("filename") != expected_filename:
            continue
        if expected_page_number is not None and item.get("page_number") != expected_page_number:
            continue
        return True
    return False
