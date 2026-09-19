# AGENTS.md — rules for every coding agent working on Praman

## Read first
1. docs/PLAN.md sections 1, 3 and 7, and the section named in your prompt.
2. contracts/schemas.py — the single source of truth for data shapes.

## Hard rules
- Edit ONLY the files listed in your prompt's OWNS line. Never edit anything else.
- Never edit contracts/schemas.py or contracts/*.json unless your prompt explicitly says so. If you believe a contract change is needed, STOP and report it in your final message instead of editing it.
- Never commit secrets. .env is git-ignored. Do not paste keys into code, tests, or logs.
- Use only fictional data. No Aadhaar numbers, no phone numbers, no real people.
- Backend imports AI ONLY via `ai_core.api`. Frontend talks ONLY to `/api/*` using `frontend/src/lib/api.ts`.
- Attestations record FACTS only: no ratings, no free text.
- Keep `AI_MODE=mock` working at all times; unit tests must not need network (mark network tests `@pytest.mark.live`).

## Working style
- Work in your own git worktree/branch. Small conventional commits (`feat(ai): ...`). Push often (every 20-30 min).
- Before finishing: run the tests named in your "definition of done", run `git diff --stat origin/main` and confirm you only touched owned files.
- Prefer simple, readable code over clever code; this is a hackathon deadline. Add short docstrings; no dead code.
- Final message must contain: what works, what's stubbed, exact run commands, and any contract change requests (if applicable).

## Structure
`contracts/` shared schemas, rules, fixtures · `ai_core/` AI + rules (Rakshit) · `backend/` FastAPI (Sukdev) · `frontend/` React (Sukdev) · `eval/` accuracy harness (Rakshit) · `data/` test inputs (Namha) · `pitch/` deck & facts (Nishtha)
