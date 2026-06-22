# LoanGuard AI — Backend Patch (Risk Detection Fix)

This patch fixes two issues:
1. The advance-fee/WhatsApp scam message that was scoring as "safe"
2. The crash on startup caused by `from __future__ import annotations`
   in `analyze.py` (already applied here too, in case you need a clean copy)

It also adds negation-awareness and decision-aware risk leveling so the
score reflects real risk instead of just counting keyword hits.

## Where each file goes

Copy each file below into your `loanguard-backend` project, **overwriting**
the existing file at that exact path. All paths are relative to your
project root (the folder containing `backend/`, `ml/`, `nlp/`, etc.):

```
loanguard-backend/
├── ml/
│   ├── keywords_config.json       ← REPLACE
│   └── keyword_extractor.py       ← REPLACE
├── nlp/
│   └── preprocessing.py           ← REPLACE
└── backend/
    ├── routers/
    │   └── analyze.py             ← REPLACE
    ├── schemas/
    │   └── response.py            ← REPLACE
    ├── services/
    │   └── analyzer.py            ← REPLACE
    └── tests/
        └── test_analyze.py        ← REPLACE
```

## How to apply

**Option A — copy the folder structure directly (recommended)**

1. Unzip `loanguard-backend-patch.zip`
2. You'll get a folder with the same `ml/`, `nlp/`, `backend/` structure
3. Copy/merge it into your existing `loanguard-backend` folder, allowing
   it to overwrite the 7 files listed above (nothing else will be touched)

**Option B — manual copy-paste**

Open each file in this patch and paste its full contents over the
matching file in your project, replacing everything in that file.

## After applying

Restart your backend:

```powershell
cd "E:\loan doc analyser\loanguard-backend"
uvicorn backend.main:app --reload --port 8000
```

Then re-run the test suite to confirm everything passes (31 tests):

```powershell
pytest backend/tests/ -q
```

Then re-test the scam message in your frontend at
`http://localhost:3000/analyze` — it should now return
`risk_level: CRITICAL`, `should_sign: false`.

## What changed (summary)

- **`ml/keywords_config.json`** — added a 9th category,
  `advance_fee_scam_signals` (CRITICAL), covering WhatsApp/SMS-style
  pre-approval advance-fee scams. Also added a few paraphrase variants
  to `hidden_fee_risk`.
- **`ml/keyword_extractor.py`** — added negation detection (so "no
  prepayment penalty" isn't scored as risky), a protective-phrase bonus
  for borrower-friendly clauses (cooling-off period, grievance redressal,
  RBI Ombudsman, etc.), and decision-aware risk leveling (2+ CRITICAL
  hits force a CRITICAL verdict regardless of document length/dilution).
- **`nlp/preprocessing.py`** — fixed a pre-existing bug where VADER's
  generic sentiment lexicon mislabeled clearly borrower-friendly
  sentences (mentioning "ombudsman," "dispute," "grievance") as
  THREATENING. Domain-specific friendly markers now correctly override
  that when no genuine aggressive language is present.
- **`backend/schemas/response.py`** — added a `negated_hits` field to
  `CategoryBreakdown` so the frontend can show "X protective mentions
  excluded from score" if desired.
- **`backend/services/analyzer.py`** — passes `negated_hits` through to
  the response.
- **`backend/routers/analyze.py`** — removed `from __future__ import
  annotations`, which was crashing FastAPI on startup (Python 3.13 +
  FastAPI 0.115.5 compatibility issue with `UploadFile` forward refs).
- **`backend/tests/test_analyze.py`** — updated the category-count
  assertion from 8 to 9.
