# AlphaForge — Claude Code Rules & Context

## What This System Is
AlphaForge is a live, deployed multi-agent AI trading analysis pipeline.
It is the foundation of a proprietary trading firm. Every code change
has real financial consequences. Treat this as production infrastructure,
not a side project.

## Architecture (read before touching anything)
- 6 bots run sequentially: macro → news → technicals → COT → debate → risk engine
- Shared state lives in shared/combined_context.json (filelock protected)
- Final verdict in shared/final_verdict.json (written by debate, read by risk)
- Dashboard: FastAPI backend (Railway) + React/Vite frontend (Vercel)
- All bot outputs POST to Railway backend via /internal/update/<botname>
- SQLite (users.db) for auth, bot_outputs table for pipeline data
- Bot outputs also saved locally as backup at <bot>/outputs/YYYY-MM-DD_<bot>.json

## Assets Tracked
- GC=F (Gold), ^GSPC (SPX), ^NDX (NQ)

## Macro Regime Parsing — CRITICAL
- Macro regime is extracted via regex: \{.*"macro_regime".*\}
- Valid values: RISK_ON, RISK_OFF, TRANSITION
- NEVER use substring matching on raw macro text
- This regex runs in run_technicals.py — do not change the output format of macro bot

## Signal Scoring System
- Scores are 0-10
- Signal strength: STRONG (8-10), SIGNAL (5-7), WEAK (3-4), NO_SIGNAL (0-2)
- Conviction maps to risk: 1-3 → 0.5%, 4-6 → 1.0%, 7-8 → 1.5%, 9-10 → 2.0% account risk
- Position sizing: dollar_risk / stop_distance. Always round DOWN. Never round up.
- NO_SIGNAL, NONE, SYSTEM_FAILURE → skip position sizing entirely (no division by zero)

## VSA Rules
- Rule 1 is SOFTENED: hard cancel only if candle closes in lower 40% of range
- Otherwise flag as ABSORPTION_POSSIBLE, do not cancel signal
- Never remove this softening without explicit instruction

## COT Bot
- Runs WEEKLY on Fridays after 3:30 PM ET (CFTC release)
- Role is INFORMATIONAL ONLY — never block or gate signals based on COT alone
- Asset codes: Gold=088691, SPX=13874A, NQ=209742
- Uses real open_interest_all column — never a proxy sum

## Weekly Gate
- weekly_gate.py runs on Mondays, loads cache other days
- Does NOT import fetch_all_assets — data is passed in as a parameter
- Do not refactor this without understanding the caching logic first

## Silent Failure Handling
- If any asset crashes in technicals bot, write signal_strength="SYSTEM_FAILURE" with error
- Never silently skip a failed asset
- system_alerts in combined_context.json must reflect all failures

## Race Condition Protection
- Every bot uses filelock on shared/combined_context.lock
- 10 second timeout before raising error
- Never write to combined_context.json without acquiring the lock first

## Dashboard Rules
- All API endpoints are JWT protected except GET /health
- Token expiry: 8 hours
- CORS is configured for Vercel domain ONLY — never open CORS to *
- Frontend auto-refreshes every 3 minutes via setInterval
- Env vars in frontend use VITE_ prefix via import.meta.env — never process.env

## Environment Variables — NEVER hardcode keys
- macro-bot/.env: FRED_API_KEY, GEMINI_API_KEY
- news-bot/.env: NEWSAPI_KEY, ALPHAVANTAGE_KEY, FRED_API_KEY
- debate-bot/.env: GEMINI_API_KEY
- dashboard/backend/.env: SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD, INTERNAL_SECRET
- dashboard/frontend/.env: VITE_API_URL
- All covered by **/.env in .gitignore — verify before every commit

## Engineering Standards
- All code is production quality — no TODOs left in merged code
- Every external API call has try/except — failures must never crash the pipeline
- Bot POST to backend is wrapped in try/except — POST failure never kills a bot run
- No print() in production paths — use the logger from run_all.py
- run_all.py stops the entire pipeline on any non-zero exit code
- Master schedule runs at 9:45 AM ET every weekday via --schedule flag
- Railway backend is pinged every 20 minutes to prevent sleep

## Trading Domain Rules (non-negotiable)
- Never suggest market orders for entries — always limit orders within entry_zone
- Stop loss is always hard, never mental
- Risk per trade never exceeds 2% of account under any conviction level
- RR ratio below 1.5 is not a valid trade — do not generate targets that produce RR < 1.5
- Direction conflicts between macro regime and technicals signal must surface as a flag, never silently resolved
- COT positioning_extreme = True is a warning, not a blocker

## What Good Output Looks Like
- Macro bot: RISK_ON/RISK_OFF/TRANSITION with structured JSON block at end
- News bot: 9 categories scored -1.0 to +1.0 with contradiction_flag and narrative_momentum
- Technicals bot: per-asset score 0-10 with all fields populated including rr_ratio, entry_zone, vsa_flag
- Debate bot: bull_case, bear_case, risk_case, synthesis, overall_conviction 0-10
- Risk engine: trade sheet with position_size, unit, direction per asset

## Hosting
- Backend: https://alphaforge-backend.railway.app (Railway, Python 3.13, us-west2)
- Frontend: https://alphaforge.vercel.app (Vercel, auto-deploy on GitHub push)
- Git client: GitHub Desktop (git not in system PATH on Windows)

## Before Making Any Change
1. Identify which bot or module is affected
2. Check if combined_context.json schema is impacted
3. Check if the change affects macro regime regex parsing
4. Check if frontend payload shape changes (would break dashboard)
5. If touching scorer.py — re-verify conviction → risk mapping is intact
