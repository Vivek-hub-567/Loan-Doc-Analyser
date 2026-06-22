# LoanGuard AI — Frontend

A Next.js 14 frontend built against the **actual** LoanGuard AI FastAPI backend
(not the original full product spec). Saffron & blue, light-mode, clean-professional
design system — calm and protective, not alarming.

## What's built

Only the pages your backend can actually power:

| Route | Backend endpoint(s) used |
|---|---|
| `/` | Landing page. Fetches `GET /categories` for the real 8 risk categories (falls back to a static copy if the API is unreachable). |
| `/dashboard/analyze` | `POST /analyze` (paste text) and `POST /analyze/file` (PDF/DOCX/TXT upload, max 5MB). |
| `/dashboard/history` | Client-side only — see note below. |
| `/dashboard/report/[id]` | `GET /history/{doc_id}` as a fallback; primarily reads from local cache. |

## What was intentionally left out, and why

Your backend has **no auth, no Supabase wiring, no alerts/proof-vault system, and no RBI guidelines
endpoint** — so Login/Register, Alerts, and Guidelines pages from the original spec were dropped
rather than built as disconnected mockups. Also dropped:

- **Image upload / OCR tab** — `file_parser.py` only handles `.pdf`, `.docx`, `.txt`. There's no OCR
  step anywhere in the backend, so an "Upload Image" tab would be fiction. Removed.
- **History as a real list** — `GET /history/{doc_id}` only fetches a *single* record; there's no
  list-all endpoint, and the database service (`backend/services/database.py`) is an **in-memory
  stub** that resets on every server restart. To make a History page work at all, analyses are
  indexed client-side in `localStorage` (via Zustand `persist`) the moment they complete. This means:
  - History is per-browser, not server-side.
  - Deleting calls `DELETE /history/{doc_id}` best-effort, but always clears locally even if the
    backend 404s (likely, after a restart).
- **Annotated document view** — `category_breakdown` only returns matched keyword *strings*, not
  character offsets (only NER entities get offsets). The report page reconstructs highlights
  client-side by re-running a case-insensitive match over the *original pasted text*, which is
  cached locally at analysis time. **File uploads can't show this view** — the extracted text isn't
  sent back by the API, so the panel says so honestly instead of faking it.
- **RBI guideline mapping / borrower action plan** — these only exist when `run_rag: true` is sent
  in `AnalysisOptions`, which is **off by default** in the backend's own schema (`backend/schemas/request.py`).
  The UI shows them when present and explains they're opt-in when absent.

## Setup

```bash
npm install
cp .env.local.example .env.local   # point NEXT_PUBLIC_API_URL at your backend
npm run dev
```

Runs on `http://localhost:3000` by default, or `http://localhost:3001` if port 3000 is already in use. Your FastAPI backend should be running on
`http://localhost:8000` (its default `.env` `allowed_origins` includes both
`http://localhost:3000` and `http://localhost:3001`, so CORS works out of the box).

## Stack

Next.js 14 (App Router) · TypeScript strict · Tailwind CSS (hand-built primitives, no shadcn CLI
dependency) · Framer Motion · Recharts · react-dropzone · Zustand (`persist` for local history) ·
TanStack Query · Axios · Zod (schemas mirror the backend's Pydantic models field-for-field) ·
sonner · Inter + Sora via `next/font/google`.

## Notes for going further

- If you wire up Supabase auth later, the dashboard layout (`src/app/dashboard/layout.tsx`) is the
  natural place to add a route guard.
- If you add a real `GET /history` list endpoint or persistent DB, swap `useHistory()` in
  `src/hooks/useHistory.ts` to fetch from the server instead of the Zustand store — the rest of the
  UI doesn't care where the data comes from.
- If you add character offsets to `category_breakdown`, the highlight logic in
  `src/lib/highlight.ts` can be simplified from substring search to direct offset slicing.
