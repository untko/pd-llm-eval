# Smoke suite v1

Initial curated benchmark derived from the supplied agriculture evaluation workbook.

## Coverage

| Behavior | Cases |
|---|---:|
| answerable | 16 |
| underspecified | 4 |
| out_of_kb | 3 |
| near_miss | 3 |
| social | 2 |
| escalate | 2 |
| **Total** | **30** |

The answerable set includes:
- direct KB retrieval
- disease/pest reasoning
- exact dosage/timing checks
- noisy Burmese text
- malformed numeric input
- two synthetic multi-turn cases derived from approved KB facts

## Quality tiers

- `silver`: answerable reference facts/answers derived from the workbook and its existing review process; not independently re-certified by an agronomy expert in this repository.
- `behavior-only`: the expected action is the primary ground truth, such as clarify, abstain, no-retrieval, or escalate.

No case is labeled `gold` yet. Promote cases to gold only after explicit expert/human verification.

## Editable source of truth

- `cases.json`: all 30 cases in pretty-printed, human-editable JSON. Edit this file for normal benchmark maintenance.
- The split JSONL files below are compatibility snapshots and should not be treated as the editable source.

## Compatibility files

- `answerable_a.jsonl`: cases 001-008
- `answerable_b.jsonl`: cases 009-016
- `underspecified.jsonl`: cases 017-020
- `out_of_kb.jsonl`: cases 021-023
- `near_miss.jsonl`: cases 024-026
- `social.jsonl`: cases 027-028
- `escalate.jsonl`: cases 029-030

The source workbook, origin UUIDs, and raw customer export are intentionally not committed to this public repository.
