# Dataset taxonomy and source-workbook learnings

The legacy evaluation workbook is useful as more than a question bank. It already contains three distinct kinds of information that should remain separate in the canonical benchmark.

## Behavioral taxonomy

The existing labels define routing behavior well:

| Label | Expected action | Meaning |
|---|---|---|
| `answerable` | `answer` | Supported by the approved KB/context |
| `underspecified` | `clarify` | Potentially answerable, but required context is missing |
| `out_of_kb` | `abstain` | Not supported by the available KB |
| `near_miss` | `abstain` | Lexically/semantically close to KB content, but not actually supported |
| `social` | `no_retrieval` | Greeting, thanks, closing, or other social turn |
| `escalate` | `escalate` | Requires a human/business process rather than KB generation |

This is the primary routing taxonomy.

## Agriculture domain taxonomy

The workbook also provides domain fields that should be preserved rather than flattened into tags:

- `category`
- `crop_group`
- `topic_code`
- `topic_title_my`
- `level`
- `subtopic`

These support slice-level evaluation by crop, practice, pest/disease topic, product, or KB depth.

## Curation/provenance metadata

Useful existing fields include:

- real vs generated source
- selection strategy such as census, real-census, representative, and spanning
- KB overlap / longest-span measures
- original intent identifier
- automated judge verdict/reason
- near-topic identifier
- ground-truth generation/review status and model

These are curation metadata, not evaluation targets.

## Failure modes surfaced by review notes

The review notes identify several cases that should be first-class regression tests:

1. **Ambiguous single-keyword queries**
   - A query may retrieve correctly while the KB is small, then become ambiguous when crop-specific FAQs are added.
   - Expected behavior should switch to clarification when crop/input context is insufficient.

2. **Keyword conflict**
   - Matching crop + input terms can over-power the actual diagnostic intent.
   - Test diagnosis questions separately from generic practice/instruction questions.

3. **Numeric parsing**
   - Plant ages/dosages can be corrupted or normalized incorrectly.
   - Add explicit numeric-preservation cases and exact-value assertions.

4. **Symptom-based pest/disease retrieval**
   - Structured pest/disease content performs well when symptoms are distinctive.
   - Preserve these as positive/golden retrieval cases.

5. **Wrong-topic but plausible responses**
   - A response can mention the correct crop/topic family while giving the wrong disease, practice, or dosage.
   - Semantic similarity alone is therefore insufficient for grading.

## Ground-truth policy

The workbook contains a mixture of human-reviewed and model-generated answers. Do not automatically promote every reference answer to gold.

Recommended use:

- human/expert-verified answers -> gold
- model-generated but reviewed/validated answers -> silver
- non-answer actions -> behavior-only
- known failures -> regression after the expected behavior is verified

## Privacy

The repository is public. Do not commit raw customer conversation exports, origin UUIDs, or the source workbook.

Keep raw ingestion files under `data/private/` or `data/raw/`, both of which are gitignored. Only publish sanitized benchmark cases after review.
