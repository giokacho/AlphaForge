# health_check.py
# =============================================================================
# AlphaForge — Full Pipeline Health Check
#
# Verifies the pipeline is wired correctly WITHOUT making any API calls.
# Run from the project root:  python health_check.py
# =============================================================================

import os
import sys
import json

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))

_passed = 0
_failed = 0
_stale_count = 0


def _pass(label: str, reason: str = "") -> None:
    global _passed
    _passed += 1
    suffix = f"  ({reason})" if reason else ""
    print(f"  PASS  {label}{suffix}")


def _fail(label: str, reason: str) -> None:
    global _failed
    _failed += 1
    print(f"  FAIL  {label}  —  {reason}")


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def p(rel: str) -> str:
    """Resolve a root-relative path."""
    return os.path.join(ROOT, rel)


# =============================================================================
# CHECK 1 — Required files exist
# =============================================================================
section("CHECK 1 · Required files across all 4 bots")

REQUIRED_FILES = [
    # macro-bot
    "macro-bot/config.py",
    "macro-bot/data_fetcher.py",
    "macro-bot/scorer.py",
    "macro-bot/report.py",
    "macro-bot/run.py",
    "macro-bot/requirements.txt",
    "macro-bot/.env",
    # news-bot
    "news-bot/config.py",
    "news-bot/run_news.py",
    "news-bot/aggregator.py",
    "news-bot/scorer.py",
    "news-bot/classifier.py",
    "news-bot/fetcher_news.py",
    "news-bot/fetcher_fred.py",
    "news-bot/fetcher_alphavantage.py",
    "news-bot/weighter.py",
    "news-bot/requirements.txt",
    "news-bot/.env",
    # technicals-bot
    "technicals-bot/config.py",
    "technicals-bot/run_technicals.py",
    "technicals-bot/data_fetcher.py",
    "technicals-bot/daily_signal.py",
    "technicals-bot/weekly_gate.py",
    "technicals-bot/entry_timer.py",
    "technicals-bot/levels.py",
    "technicals-bot/vsa_check.py",
    "technicals-bot/scorer.py",
    "technicals-bot/requirements.txt",
    # debate-bot
    "debate-bot/config.py",
    "debate-bot/run_debate.py",
    "debate-bot/data_assembler.py",
    "debate-bot/debaters.py",
    "debate-bot/synthesizer.py",
    "debate-bot/requirements.txt",
    "debate-bot/.env",
    # shared
    "shared/combined_context.json",
    # root
    ".gitignore",
]

for rel in REQUIRED_FILES:
    if os.path.isfile(p(rel)):
        _pass(rel)
    else:
        _fail(rel, "file not found")


# =============================================================================
# CHECK 2 — Imports resolve without errors
# =============================================================================
section("CHECK 2 · Import resolution (no API calls made)")

# Each entry: (display_name, bot_dir_relative_to_root, module_name)
IMPORTS = [
    ("macro-bot · config",        "macro-bot",       "config"),
    ("macro-bot · data_fetcher",  "macro-bot",       "data_fetcher"),
    ("macro-bot · scorer",        "macro-bot",       "scorer"),
    ("macro-bot · report",        "macro-bot",       "report"),
    ("news-bot · config",         "news-bot",        "config"),
    ("news-bot · aggregator",     "news-bot",        "aggregator"),
    ("news-bot · classifier",     "news-bot",        "classifier"),
    ("news-bot · scorer",         "news-bot",        "scorer"),
    ("news-bot · weighter",       "news-bot",        "weighter"),
    ("technicals-bot · config",   "technicals-bot",  "config"),
    ("technicals-bot · scorer",   "technicals-bot",  "scorer"),
    ("technicals-bot · daily_signal", "technicals-bot", "daily_signal"),
    ("technicals-bot · weekly_gate",  "technicals-bot", "weekly_gate"),
    ("technicals-bot · vsa_check",    "technicals-bot", "vsa_check"),
    ("debate-bot · config",       "debate-bot",      "config"),
    ("debate-bot · data_assembler","debate-bot",     "data_assembler"),
    ("debate-bot · synthesizer",  "debate-bot",      "synthesizer"),
]

import importlib

for display, bot_dir, module in IMPORTS:
    bot_path = p(bot_dir)
    if bot_path not in sys.path:
        sys.path.insert(0, bot_path)
    try:
        importlib.import_module(module)
        _pass(display)
    except Exception as exc:
        _fail(display, str(exc)[:120])


# =============================================================================
# CHECK 3 — shared/combined_context.json structure
# =============================================================================
section("CHECK 3 · shared/combined_context.json structure")

ctx_path = p("shared/combined_context.json")
REQUIRED_KEYS = ["macro_data", "news_data", "technicals_data", "combined_risk_level"]

if not os.path.isfile(ctx_path):
    _fail("combined_context.json", "file not found")
else:
    try:
        with open(ctx_path, "r", encoding="utf-8") as f:
            ctx = json.load(f)
        _pass("combined_context.json", "file is valid JSON")
        for key in REQUIRED_KEYS:
            if key in ctx:
                val = ctx[key]
                hint = f"= {repr(val)[:60]}" if not isinstance(val, dict) else f"(dict, {len(val)} keys)"
                _pass(f"  key · {key}", hint)
            else:
                _fail(f"  key · {key}", "key missing from combined_context.json")
    except json.JSONDecodeError as exc:
        _fail("combined_context.json", f"invalid JSON — {exc}")


# =============================================================================
# CHECK 4 — .env files contain non-empty, non-placeholder keys
# =============================================================================
section("CHECK 4 · .env files — keys populated (not placeholder)")

PLACEHOLDER = "your_key_here"

ENV_CHECKS = {
    "macro-bot/.env":  ["GEMINI_API_KEY", "FRED_API_KEY"],
    "news-bot/.env":   ["GEMINI_API_KEY", "NEWSAPI_KEY", "ALPHAVANTAGE_KEY", "FRED_API_KEY"],
    "debate-bot/.env": ["GEMINI_API_KEY"],
}

for env_rel, required_keys in ENV_CHECKS.items():
    env_path = p(env_rel)
    if not os.path.isfile(env_path):
        _fail(env_rel, "file not found")
        continue

    # Parse the .env file manually (avoid importing dotenv side-effects here)
    env_vars: dict[str, str] = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env_vars[k.strip()] = v.strip()

    for key in required_keys:
        val = env_vars.get(key, "")
        if not val:
            _fail(f"  {env_rel} · {key}", "key is missing or empty")
        elif val == PLACEHOLDER:
            _fail(f"  {env_rel} · {key}", "still set to placeholder 'your_key_here'")
        else:
            _pass(f"  {env_rel} · {key}", f"{val[:6]}{'*' * max(0, len(val) - 6)}")


# =============================================================================
# CHECK 5 — technicals-bot/outputs/weekly_gate.json exists
# =============================================================================
section("CHECK 5 · technicals-bot/outputs/weekly_gate.json")

wg_path = p("technicals-bot/outputs/weekly_gate.json")
if not os.path.isfile(wg_path):
    _fail("weekly_gate.json", "file not found — run run_technicals.py first")
else:
    try:
        with open(wg_path, "r", encoding="utf-8") as f:
            wg = json.load(f)
        assets_found = list(wg.keys())
        _pass("weekly_gate.json", f"assets: {assets_found}")
    except json.JSONDecodeError as exc:
        _fail("weekly_gate.json", f"invalid JSON — {exc}")


# =============================================================================
# CHECK 6 — Data freshness check
# =============================================================================
section("CHECK 6 · Data freshness check")

import time
import glob

def check_freshness(filepath: str, max_age_hours: int, glob_pattern: bool = False):
    global _stale_count
    
    actual_path = filepath
    if glob_pattern:
        files = glob.glob(filepath)
        if not files:
            _fail(os.path.basename(filepath), "no files found matching pattern")
            _stale_count += 1
            return
        actual_path = max(files, key=os.path.getmtime)
    else:
        if not os.path.isfile(actual_path):
            _fail(os.path.basename(actual_path), "file not found")
            _stale_count += 1
            return
            
    mtime = os.path.getmtime(actual_path)
    age_seconds = time.time() - mtime
    age_hours = age_seconds / 3600.0
    
    filename = os.path.basename(actual_path)
    if age_hours > max_age_hours:
        _fail(filename, f"STALE (age: {age_hours:.1f}h > {max_age_hours}h limit)")
        _stale_count += 1
    else:
        _pass(filename, f"age: {age_hours:.1f}h (limit: {max_age_hours}h)")

# 1. weekly_gate.json -> max 7 days (168h)
check_freshness(p("technicals-bot/outputs/weekly_gate.json"), 168)

# 2. shared/combined_context.json -> max 24h
check_freshness(p("shared/combined_context.json"), 24)

# 3. YYYY-MM-DD outputs -> max 24h
check_freshness(p("technicals-bot/outputs/*_technicals.json"), 24, glob_pattern=True)
check_freshness(p("cot-bot/outputs/*_cot.json"), 24, glob_pattern=True)
check_freshness(p("news-bot/outputs/*_news_scores.json"), 24, glob_pattern=True)


# =============================================================================
# FINAL SUMMARY
# =============================================================================
total = _passed + _failed
print(f"\n{'=' * 60}")
print(f"  HEALTH CHECK COMPLETE")
print(f"  Passed       : {_passed} / {total}")
print(f"  Failed       : {_failed} / {total}")
print(f"  Stale files  : {_stale_count}")
if _failed == 0:
    print(f"  Status       : ALL SYSTEMS GO")
else:
    print(f"  Status       : {_failed} issue(s) need attention")
print(f"{'=' * 60}\n")

if _stale_count > 0:
    print("WARNING: Stale data detected — do not run debate bot until pipeline is refreshed.")
