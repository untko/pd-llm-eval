from __future__ import annotations

import json
from pathlib import Path

from .models import EvalCase


class KnowledgeBase:
    """Read-only resolver for the team's parsed agriculture KB."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        articles = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(articles, list):
            raise TypeError(f"{self.path}: expected a JSON array of KB articles")

        self.articles_by_code: dict[str, dict] = {}
        self.sections_by_id: dict[str, tuple[dict, dict]] = {}

        for article in articles:
            code = article["code"]
            self.articles_by_code[code] = article
            for section in article.get("subtopics", []):
                self.sections_by_id[section["id"]] = (article, section)

    def has_source(self, source_id: str) -> bool:
        if source_id.endswith("/topic-general"):
            code = source_id.split("/", 1)[0]
            return code in self.articles_by_code
        return source_id in self.sections_by_id

    def resolve(self, source_id: str) -> str:
        """Return authoritative Burmese source text for one canonical source id."""
        if source_id.endswith("/topic-general"):
            code = source_id.split("/", 1)[0]
            article = self.articles_by_code.get(code)
            if article is None:
                raise KeyError(source_id)

            parts: list[str] = []
            intro = str(article.get("intro") or "").strip()
            if intro:
                parts.append(f"INTRO:\n{intro}")
            for section in article.get("subtopics", []):
                content = str(section.get("content") or "").strip()
                parts.append(
                    f"SECTION [{section['id']}] {section.get('name', '')}:\n{content}"
                )
            return "\n\n".join(parts)

        resolved = self.sections_by_id.get(source_id)
        if resolved is None:
            raise KeyError(source_id)

        article, section = resolved
        return (
            f"SECTION [{source_id}] {article.get('title_en', '')} / "
            f"{section.get('name', '')}:\n{section.get('content', '')}"
        )

    def context_for_case(self, case: EvalCase) -> str | None:
        if not case.gold_sources:
            return None

        blocks = []
        for source in case.gold_sources:
            blocks.append(self.resolve(source.source_id))
        return "\n\n".join(blocks)


def validate_case_sources(cases: list[EvalCase], kb: KnowledgeBase) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for case in cases:
        for source in case.gold_sources:
            if not kb.has_source(source.source_id):
                missing.append({"case_id": case.case_id, "source_id": source.source_id})
    return missing
