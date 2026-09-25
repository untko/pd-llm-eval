import json

from pd_llm_eval.kb import KnowledgeBase, validate_case_sources
from pd_llm_eval.models import EvalCase


def _write_kb(path):
    path.write_text(
        json.dumps(
            [
                {
                    "code": "ABC",
                    "title_en": "Example",
                    "intro": "Article intro",
                    "subtopics": [
                        {
                            "id": "ABC/1-How_to",
                            "name": "How to",
                            "content": "Use exactly four spoons.",
                        },
                        {
                            "id": "ABC/2-Warnings",
                            "name": "Warnings",
                            "content": "Do not apply at noon.",
                        },
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _case(source_id: str) -> EvalCase:
    return EvalCase.model_validate(
        {
            "case_id": "qa.001",
            "name": "Example",
            "language": "en",
            "user_input": "How much?",
            "behavior_label": "answerable",
            "expected_action": "answer",
            "evaluation_focus": ["generation"],
            "expected_behavior": ["Use the source"],
            "gold_sources": [{"source_id": source_id}],
        }
    )


def test_resolve_exact_section(tmp_path):
    path = tmp_path / "kb.json"
    _write_kb(path)
    kb = KnowledgeBase(path)

    text = kb.resolve("ABC/1-How_to")

    assert "Use exactly four spoons." in text
    assert "Do not apply at noon." not in text


def test_resolve_topic_general_uses_full_article(tmp_path):
    path = tmp_path / "kb.json"
    _write_kb(path)
    kb = KnowledgeBase(path)

    text = kb.resolve("ABC/topic-general")

    assert "Article intro" in text
    assert "Use exactly four spoons." in text
    assert "Do not apply at noon." in text


def test_validate_case_sources_reports_missing(tmp_path):
    path = tmp_path / "kb.json"
    _write_kb(path)
    kb = KnowledgeBase(path)

    missing = validate_case_sources([_case("ABC/missing")], kb)

    assert missing == [{"case_id": "qa.001", "source_id": "ABC/missing"}]
