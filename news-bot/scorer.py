# scorer.py
# Final signal scoring engine for AlphaForge news-bot.
# Accepts a base conviction score (0–10), a trade direction, and an optional
# combined_context dict read from shared/combined_context.json.
#
# Pipeline role: sits after aggregation and before orchestrator export.
# Steps 6-10 are appended to whatever Steps 1-5 produced upstream.

import json
import os

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_macro_regime(combined_context: dict) -> str:
    """
    Pull the macro regime string from combined_context.
    Checks macro_data sub-dict first (structured JSON from macro-bot),
    then falls back to the top-level macro_regime key written by run_news.py.
    Returns one of: RISK_ON | RISK_OFF | TRANSITION | UNKNOWN
    """
    macro_data = combined_context.get("macro_data", {})

    # macro_data may be stored as a raw markdown string when the macro-bot
    # report hasn't been re-parsed — handle both forms defensively.
    if isinstance(macro_data, dict):
        regime = (
            macro_data.get("regime_label")
            or macro_data.get("regime")
            or combined_context.get("macro_regime", "UNKNOWN")
        )
    else:
        # Fall back: scan top-level or the raw string for known tokens
        regime = combined_context.get("macro_regime", "UNKNOWN")
        if regime == "UNKNOWN" and isinstance(macro_data, str):
            upper = macro_data.upper()
            if "RISK_OFF" in upper or "RISK OFF" in upper:
                regime = "RISK_OFF"
            elif "RISK_ON" in upper or "RISK ON" in upper:
                regime = "RISK_ON"
            elif "TRANSITION" in upper:
                regime = "TRANSITION"

    return str(regime).upper().strip() if regime else "UNKNOWN"


def _resolve_contradiction_flag(combined_context: dict) -> bool:
    """
    Pull the contradiction_flag from combined_context.
    It lives under news_data.contradiction_flag (set by aggregator.py).
    """
    news_data = combined_context.get("news_data", {})
    if isinstance(news_data, dict):
        return bool(news_data.get("contradiction_flag", False))
    return False


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def calculate_final_score(
    base_score: float,
    signal_direction: str,
    combined_context: dict = None
) -> dict:
    """
    Applies Steps 6–10 of the AlphaForge scoring pipeline to convert a raw
    conviction score into a trade-ready signal with position sizing guidance.

    Parameters
    ----------
    base_score : float
        The conviction score produced by Steps 1–5 (0.0 – 10.0 scale).
    signal_direction : str
        Trade direction: 'LONG' or 'SHORT'.
    combined_context : dict, optional
        The full parsed contents of shared/combined_context.json.
        When None, macro and news adjustments are skipped.

    Returns
    -------
    dict with keys:
        base_score              – original score before Steps 6-10
        adjusted_score          – score after macro multiplier + news penalty
        final_score             – adjusted_score capped at 10.0
        signal_strength         – STRONG | SIGNAL | WEAK | NO_SIGNAL
        position_size           – 100 | 75 | 50 | 0  (% of normal size)
        macro_regime            – resolved regime string (or None if no context)
        macro_multiplier_used   – float multiplier applied in Step 6
        news_penalty_applied    – float penalty applied in Step 7
        signal_direction        – echoed back for downstream consumers
    """
    direction = str(signal_direction).upper().strip()

    # -----------------------------------------------------------------------
    # Step 6 — Macro multiplier
    # -----------------------------------------------------------------------
    macro_multiplier = 1.0
    macro_regime = None

    if combined_context is not None:
        macro_regime = _resolve_macro_regime(combined_context)

        # Align / Contradict logic
        aligned_long  = (macro_regime == "RISK_ON"  and direction == "LONG")
        aligned_short = (macro_regime == "RISK_OFF" and direction == "SHORT")
        counter_long  = (macro_regime == "RISK_OFF" and direction == "LONG")
        counter_short = (macro_regime == "RISK_ON"  and direction == "SHORT")

        if aligned_long or aligned_short:
            macro_multiplier = 1.2      # Regime confirms the trade
        elif counter_long or counter_short:
            macro_multiplier = 0.75     # Regime opposes the trade
        else:
            macro_multiplier = 1.0      # TRANSITION or UNKNOWN — neutral

    adjusted_score = base_score * macro_multiplier

    # -----------------------------------------------------------------------
    # Step 7 — News penalty (contradiction flag)
    # -----------------------------------------------------------------------
    news_penalty = 0.0

    if combined_context is not None:
        if _resolve_contradiction_flag(combined_context):
            news_penalty = -0.4
            adjusted_score += news_penalty

    # -----------------------------------------------------------------------
    # Step 8 — Cap final score at 10.0
    # -----------------------------------------------------------------------
    final_score = min(adjusted_score, 10.0)
    # Floor at 0 to keep scores non-negative and meaningful
    final_score = max(final_score, 0.0)

    # -----------------------------------------------------------------------
    # Step 9 — Signal strength label
    # -----------------------------------------------------------------------
    if final_score >= 8.5:
        signal_strength = "STRONG"
    elif final_score >= 7.0:
        signal_strength = "SIGNAL"
    elif final_score >= 6.5:
        signal_strength = "WEAK"
    else:
        signal_strength = "NO_SIGNAL"

    # -----------------------------------------------------------------------
    # Step 10 — Position size (% of normal allocation)
    # -----------------------------------------------------------------------
    position_size_map = {
        "STRONG":    100,
        "SIGNAL":    75,
        "WEAK":      50,
        "NO_SIGNAL": 0,
    }
    position_size = position_size_map[signal_strength]

    # -----------------------------------------------------------------------
    # Return consolidated result dict
    # -----------------------------------------------------------------------
    return {
        "base_score":            round(base_score, 4),
        "adjusted_score":        round(adjusted_score, 4),
        "final_score":           round(final_score, 4),
        "signal_strength":       signal_strength,
        "position_size":         position_size,
        "macro_regime":          macro_regime,
        "macro_multiplier_used": macro_multiplier,
        "news_penalty_applied":  news_penalty,
        "signal_direction":      direction,
    }


# ---------------------------------------------------------------------------
# Convenience loader — reads shared/combined_context.json automatically
# ---------------------------------------------------------------------------

def load_combined_context(project_root: str = None) -> dict | None:
    """
    Attempts to load shared/combined_context.json relative to the project root.
    Returns the parsed dict on success, or None if the file is missing/corrupt.
    """
    if project_root is None:
        # Infer project root as two levels up from this file
        # (.../AlphaForge V2.2/Antigravity - AphaForge V2.2/news-bot/scorer.py)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    file_path = os.path.join(project_root, "shared", "combined_context.json")

    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[scorer] Warning: could not load combined_context.json — {e}")
        return None


# ---------------------------------------------------------------------------
# __main__ — self-contained test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("scorer.py — calculate_final_score self-test")
    print("=" * 60)

    # --- Test 1: RISK_ON + LONG  →  multiplier 1.2 ---
    ctx_risk_on = {
        "macro_data": {"regime_label": "RISK_ON"},
        "news_data":  {"contradiction_flag": False}
    }
    r1 = calculate_final_score(7.5, "LONG", ctx_risk_on)
    print("\n[Test 1] RISK_ON + LONG (expects x1.2, no penalty)")
    print(json.dumps(r1, indent=2))
    assert r1["macro_multiplier_used"] == 1.2,     "Test 1 multiplier failed"
    assert r1["news_penalty_applied"]  == 0.0,     "Test 1 penalty failed"
    assert r1["final_score"]           == 9.0,     "Test 1 final score failed"
    assert r1["signal_strength"]       == "STRONG", "Test 1 strength failed"   # 9.0 >= 8.5 → STRONG
    assert r1["position_size"]         == 100,      "Test 1 position size failed"

    # --- Test 2: RISK_OFF + SHORT  →  multiplier 1.2 ---
    ctx_risk_off = {
        "macro_data": {"regime_label": "RISK_OFF"},
        "news_data":  {"contradiction_flag": False}
    }
    r2 = calculate_final_score(7.5, "SHORT", ctx_risk_off)
    print("\n[Test 2] RISK_OFF + SHORT (expects x1.2, no penalty)")
    print(json.dumps(r2, indent=2))
    assert r2["macro_multiplier_used"] == 1.2

    # --- Test 3: RISK_ON + SHORT  →  multiplier 0.75 ---
    r3 = calculate_final_score(8.0, "SHORT", ctx_risk_on)
    print("\n[Test 3] RISK_ON + SHORT (expects x0.75, no penalty)")
    print(json.dumps(r3, indent=2))
    assert r3["macro_multiplier_used"] == 0.75
    assert r3["final_score"] == 6.0
    assert r3["signal_strength"] == "NO_SIGNAL"
    assert r3["position_size"] == 0

    # --- Test 4: RISK_OFF + LONG  →  multiplier 0.75 ---
    r4 = calculate_final_score(8.0, "LONG", ctx_risk_off)
    print("\n[Test 4] RISK_OFF + LONG (expects x0.75, no penalty)")
    print(json.dumps(r4, indent=2))
    assert r4["macro_multiplier_used"] == 0.75

    # --- Test 5: TRANSITION  →  multiplier 1.0 ---
    ctx_transition = {
        "macro_data": {"regime_label": "TRANSITION"},
        "news_data":  {"contradiction_flag": False}
    }
    r5 = calculate_final_score(8.0, "LONG", ctx_transition)
    print("\n[Test 5] TRANSITION (expects x1.0, no penalty)")
    print(json.dumps(r5, indent=2))
    assert r5["macro_multiplier_used"] == 1.0

    # --- Test 6: Contradiction flag  →  -0.4 penalty ---
    ctx_contradiction = {
        "macro_data": {"regime_label": "RISK_ON"},
        "news_data":  {"contradiction_flag": True}
    }
    r6 = calculate_final_score(7.5, "LONG", ctx_contradiction)
    print("\n[Test 6] RISK_ON + LONG + contradiction (x1.2 then -0.4)")
    print(json.dumps(r6, indent=2))
    # 7.5 * 1.2 = 9.0 - 0.4 = 8.6
    assert r6["news_penalty_applied"] == -0.4
    assert r6["final_score"] == 8.6
    assert r6["signal_strength"] == "STRONG"
    assert r6["position_size"] == 100

    # --- Test 7: Cap at 10.0 ---
    r7 = calculate_final_score(9.5, "LONG", ctx_risk_on)
    print("\n[Test 7] Cap test (9.5 * 1.2 = 11.4 -> capped at 10.0)")
    print(json.dumps(r7, indent=2))
    assert r7["final_score"] == 10.0
    assert r7["signal_strength"] == "STRONG"

    # --- Test 8: No context (no macro/news adjustments) ---
    r8 = calculate_final_score(7.0, "LONG", None)
    print("\n[Test 8] No context (no adjustments)")
    print(json.dumps(r8, indent=2))
    assert r8["macro_multiplier_used"] == 1.0
    assert r8["news_penalty_applied"]  == 0.0
    assert r8["macro_regime"] is None
    assert r8["signal_strength"] == "SIGNAL"
    assert r8["position_size"] == 75

    # --- Test 9: Signal strength boundary checks ---
    # 8.5 → STRONG
    r9a = calculate_final_score(8.5, "LONG", None)
    assert r9a["signal_strength"] == "STRONG",    f"Expected STRONG, got {r9a['signal_strength']}"
    # 7.0 → SIGNAL
    r9b = calculate_final_score(7.0, "LONG", None)
    assert r9b["signal_strength"] == "SIGNAL",    f"Expected SIGNAL, got {r9b['signal_strength']}"
    # 6.5 → WEAK
    r9c = calculate_final_score(6.5, "LONG", None)
    assert r9c["signal_strength"] == "WEAK",      f"Expected WEAK, got {r9c['signal_strength']}"
    # 6.49 → NO_SIGNAL
    r9d = calculate_final_score(6.49, "LONG", None)
    assert r9d["signal_strength"] == "NO_SIGNAL", f"Expected NO_SIGNAL, got {r9d['signal_strength']}"
    print("\n[Test 9] All boundary checks passed.")

    print("\n" + "=" * 60)
    print("All tests passed.")
    print("=" * 60)
