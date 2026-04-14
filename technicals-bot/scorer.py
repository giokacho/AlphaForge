# scorer.py  —  AlphaForge technicals-bot
# =============================================================================
# calculate_final_score()
#
# Aggregates every upstream module into one trade-ready signal dict.
# The return value is intentionally verbose: every intermediate step is
# preserved so the orchestrator, the debate-bot, and any future UI can
# audit exactly why a score ended up where it did.
#
# Input dicts (produced by other modules in this package):
#   daily_signal   — from daily_signal.calculate_daily_signal()
#   entry_timer    — from entry_timer.check_entry()
#   vsa_check      — from vsa_check.run_vsa_check()
#   weekly_gate    — from weekly_gate.calculate_weekly_gate()   (or loaded JSON)
#   stops_targets  — from levels.calculate_stops_and_targets()   (optional)
#   atr_regime     — from levels.calculate_atr_regime()           (optional)
#   combined_context — shared/combined_context.json               (optional)
# =============================================================================

import json
import os


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_macro_regime(combined_context: dict) -> str:
    """
    Safely pull the macro regime string from combined_context.
    Handles both structured dict and raw markdown string forms.
    Returns one of: RISK_ON | RISK_OFF | TRANSITION | UNKNOWN
    """
    macro_data = combined_context.get("macro_data", {})

    if isinstance(macro_data, dict):
        regime = (
            macro_data.get("regime_label")
            or macro_data.get("regime")
            or combined_context.get("macro_regime", "UNKNOWN")
        )
    else:
        # Fall back: check top-level key or scan raw markdown string
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
    Check news_data.contradiction_flag in combined_context (set by aggregator.py).
    Falls back to top-level contradiction_flag for backwards compatibility.
    """
    news_data = combined_context.get("news_data", {})
    if isinstance(news_data, dict):
        flag = news_data.get("contradiction_flag", False)
    else:
        flag = combined_context.get("contradiction_flag", False)
    return bool(flag)


def _format_entry_zone(entry_zone) -> str:
    """Returns a tidy string like '5210.34 – 5231.17' or 'N/A'."""
    if not entry_zone or len(entry_zone) < 2:
        return "N/A"
    return f"{entry_zone[0]:.2f} - {entry_zone[1]:.2f}"


def _atr_regime_label(atr_percentile: float) -> str:
    if atr_percentile > 70:
        return "HIGH_VOL"
    elif atr_percentile < 30:
        return "LOW_VOL"
    return "NORMAL_VOL"


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def calculate_final_score(
    daily_signal:    dict,
    entry_timer:     dict,
    vsa_check:       dict,
    weekly_gate:     dict,
    stops_targets:   dict = None,
    atr_regime:      dict = None,
    combined_context: dict = None
) -> dict:
    """
    Converts upstream module outputs into a fully-annotated final score dict.

    Steps
    -----
    1.  Gate check      — hard-bail if entry not confirmed or VSA hard_cancel
    2.  Base score      — derived from daily factor count (total_score abs value)
    3.  Quality bonus   — 4H entry conditions (PULLBACK / BREAKOUT)
    4.  VSA adjustment  — score_adjustment from vsa_check module
    5.  Flag bonuses    — FRESH_CROSS, deeper_pullback, STRUCTURE_CONFLICT
    6.  Weekly cap      — ADX-driven score ceiling from weekly_gate
    7.  Macro multiplier — regime vs trade direction (Steps 6 in pipeline spec)
    8.  News penalty    — contradiction_flag deduction                (Step 7)
    9.  Final cap       — hard ceiling at 10.0, floored at 0.0       (Step 8)
    10. Signal strength — STRONG / SIGNAL / WEAK / NO_SIGNAL         (Step 9)
    11. Position size   — 100 / 75 / 50 / 0 pct                     (Step 10)

    Returns
    -------
    Full audit dict — every field listed in the module docstring above.
    """
    stops_targets  = stops_targets  or {}
    atr_regime     = atr_regime     or {}
    reasons: list[str] = []

    # ------------------------------------------------------------------
    # Step 1 — Gate check
    # ------------------------------------------------------------------
    entry_confirmed = entry_timer.get("entry_confirmed", False)
    hard_cancel     = vsa_check.get("hard_cancel", False)
    sig             = daily_signal.get("signal", "NO_SIGNAL")

    if not entry_confirmed or hard_cancel:
        reason = (
            "VSA hard-cancel overrides all signals — no trade."
            if hard_cancel
            else "4H entry not confirmed — insufficient pullback/breakout conditions met."
        )
        return {
            # Scoring trail
            "base_score":           0.0,
            "quality_bonus":        0.0,
            "vsa_adjustment":       0.0,
            "flag_adjustments":     0.0,
            "weekly_cap_applied":   False,
            "macro_multiplier_used": 1.0,
            "news_penalty_applied": 0.0,
            "final_score":          0.0,
            # Signal
            "signal_strength":      "NO_SIGNAL",
            "direction":            sig,
            "position_size_pct":    0,
            # Risk levels
            "stop_loss":            stops_targets.get("stop_loss",  0.0),
            "target_1":             stops_targets.get("target_1",   0.0),
            "target_2":             stops_targets.get("target_2",   0.0),
            "rr_ratio":             stops_targets.get("rr_ratio",   0.0),
            "entry_zone":           _format_entry_zone(entry_timer.get("entry_zone")),
            # Context labels
            "vsa_flag":             vsa_check.get("vsa_flag", "HARD_CANCEL" if hard_cancel else "NONE"),
            "weekly_gate_summary":  weekly_gate.get("gate", "UNKNOWN"),
            "atr_regime":           _atr_regime_label(atr_regime.get("atr_percentile", 50.0)),
            "macro_regime":         None,
            # Audit
            "reasons":              [reason],
        }

    # ------------------------------------------------------------------
    # Step 2 — Base score from daily factor total
    # ------------------------------------------------------------------
    total_factor_score = abs(daily_signal.get("total_score", 0))
    if total_factor_score == 4:
        base_score = 8.0
        reasons.append("All 4 daily factors aligned — base score set to 8.0.")
    elif total_factor_score == 3:
        base_score = 6.5
        reasons.append("3 of 4 daily factors aligned — base score set to 6.5.")
    else:
        base_score = 5.0
        reasons.append(f"Only {total_factor_score} daily factors aligned — base score set to 5.0 (low conviction).")

    running_score = base_score

    # ------------------------------------------------------------------
    # Step 3 — 4H quality bonus
    # ------------------------------------------------------------------
    mode       = entry_timer.get("mode", "")
    conditions = entry_timer.get("conditions", {})
    quality_bonus = 0.0

    if mode == "PULLBACK":
        conds_met = sum([
            conditions.get("cond_a_ema_touch",    False),
            conditions.get("cond_b_macd_turn",    False),
            conditions.get("cond_c_struct_prox",  False),
        ])
        if conds_met == 3:
            quality_bonus = 1.0
            reasons.append("PULLBACK mode: all 3 entry conditions met — quality bonus +1.0.")
        elif conds_met >= 2:
            quality_bonus = 0.5
            reasons.append(f"PULLBACK mode: {conds_met}/3 entry conditions met — quality bonus +0.5.")
        else:
            reasons.append(f"PULLBACK mode: only {conds_met}/3 conditions met — no quality bonus.")

    elif mode == "BREAKOUT":
        conds_met = sum([
            conditions.get("cond_x_price_break", False),
            conditions.get("cond_y_vol_break",   False),
        ])
        if conds_met == 2:
            quality_bonus = 1.0
            reasons.append("BREAKOUT mode: both breakout conditions confirmed — quality bonus +1.0.")
        else:
            reasons.append("BREAKOUT mode: not all breakout conditions confirmed — no quality bonus.")

    running_score += quality_bonus

    # ------------------------------------------------------------------
    # Step 4 — VSA adjustment
    # ------------------------------------------------------------------
    vsa_adjustment = vsa_check.get("score_adjustment", 0.0)
    vsa_flag       = vsa_check.get("vsa_flag", "NONE")

    if vsa_adjustment > 0:
        reasons.append(f"VSA supportive ({vsa_flag}) — score adjusted +{vsa_adjustment:.1f}.")
    elif vsa_adjustment < 0:
        reasons.append(f"VSA weakening ({vsa_flag}) — score adjusted {vsa_adjustment:.1f}.")
    else:
        reasons.append(f"VSA neutral ({vsa_flag}) — no score adjustment.")

    running_score += vsa_adjustment

    # ------------------------------------------------------------------
    # Step 5 — Flag bonuses/penalties
    # ------------------------------------------------------------------
    flag_adj   = 0.0
    daily_flags = daily_signal.get("flags", {})

    if daily_flags.get("FRESH_CROSS", False) or weekly_gate.get("FRESH_CROSS", False):
        flag_adj += 0.3
        reasons.append("FRESH MACD cross detected — flag bonus +0.3.")

    if conditions.get("deeper_pullback", False):
        flag_adj += 0.3
        reasons.append("Deeper pullback to 50-EMA confirmed — flag bonus +0.3.")

    if daily_flags.get("STRUCTURE_CONFLICT", False) or weekly_gate.get("STRUCTURE_CONFLICT", False):
        flag_adj -= 0.5
        reasons.append("Structure conflict with weekly gate bias — flag penalty -0.5.")

    if flag_adj != 0.0:
        running_score += flag_adj
    else:
        reasons.append("No flag bonuses or penalties applied.")

    # ------------------------------------------------------------------
    # Step 6 — Weekly cap (ADX-driven ceiling from weekly_gate)
    # ------------------------------------------------------------------
    score_cap     = weekly_gate.get("score_cap", 10.0)
    adx_quality   = weekly_gate.get("adx_quality", "UNKNOWN")
    weekly_gate_gate = weekly_gate.get("gate", "UNKNOWN")

    pre_cap_score     = running_score
    capped_score      = min(running_score, score_cap)
    weekly_cap_applied = capped_score < pre_cap_score

    if weekly_cap_applied:
        reasons.append(
            f"Weekly ADX quality '{adx_quality}' caps score at {score_cap:.1f} "
            f"(was {pre_cap_score:.2f})."
        )
    else:
        reasons.append(
            f"Weekly ADX quality '{adx_quality}' — cap at {score_cap:.1f} not triggered."
        )

    # ------------------------------------------------------------------
    # Step 7 — Macro multiplier (Steps 6 of pipeline specification)
    # ------------------------------------------------------------------
    macro_multiplier = 1.0
    macro_regime     = None

    if combined_context:
        macro_regime = _resolve_macro_regime(combined_context)
        direction    = sig  # LONG or SHORT

        aligned_long  = (macro_regime == "RISK_ON"  and direction == "LONG")
        aligned_short = (macro_regime == "RISK_OFF" and direction == "SHORT")
        counter_long  = (macro_regime == "RISK_OFF" and direction == "LONG")
        counter_short = (macro_regime == "RISK_ON"  and direction == "SHORT")

        if aligned_long or aligned_short:
            macro_multiplier = 1.2
            reasons.append(
                f"Macro regime '{macro_regime}' aligns with {direction} trade — multiplier x1.2."
            )
        elif counter_long or counter_short:
            macro_multiplier = 0.75
            reasons.append(
                f"Macro regime '{macro_regime}' opposes {direction} trade — multiplier x0.75."
            )
        else:
            macro_multiplier = 1.0
            reasons.append(
                f"Macro regime '{macro_regime}' — neutral, multiplier x1.0."
            )
    else:
        reasons.append("No combined_context provided — macro multiplier x1.0 (no adjustment).")

    capped_score *= macro_multiplier

    # ------------------------------------------------------------------
    # Step 8 — News penalty (Step 7 of pipeline specification)
    # ------------------------------------------------------------------
    news_penalty = 0.0

    if combined_context and _resolve_contradiction_flag(combined_context):
        news_penalty = -0.4
        capped_score += news_penalty
        reasons.append("News contradiction flag active — penalty -0.4 applied.")
    else:
        reasons.append("No news contradiction flag — no penalty.")

    # ------------------------------------------------------------------
    # Step 9 — Final cap at 10.0, floor at 0.0 (Step 8 of pipeline spec)
    # ------------------------------------------------------------------
    final_score = round(min(max(capped_score, 0.0), 10.0), 4)

    if capped_score > 10.0:
        reasons.append(f"Score {capped_score:.2f} exceeded ceiling — capped at 10.0.")
    if capped_score < 0.0:
        reasons.append(f"Score {capped_score:.2f} went negative — floored at 0.0.")

    # ------------------------------------------------------------------
    # Step 10 — Signal strength (Step 9 of pipeline specification)
    # ------------------------------------------------------------------
    if final_score >= 8.5:
        signal_strength = "STRONG"
    elif final_score >= 7.0:
        signal_strength = "SIGNAL"
    elif final_score >= 6.5:
        signal_strength = "WEAK"
    else:
        signal_strength = "NO_SIGNAL"

    # ------------------------------------------------------------------
    # Step 11 — Position size (Step 10 of pipeline specification)
    # ------------------------------------------------------------------
    pos_map = {
        "STRONG":    100,
        "SIGNAL":    75,
        "WEAK":      50,
        "NO_SIGNAL": 0,
    }
    position_size_pct = pos_map[signal_strength]

    # If NO_SIGNAL suppress direction as well
    direction_out = sig if signal_strength != "NO_SIGNAL" else "NONE"

    # ------------------------------------------------------------------
    # ATR regime label
    # ------------------------------------------------------------------
    atr_pct   = atr_regime.get("atr_percentile", 50.0)
    atr_label = _atr_regime_label(atr_pct)

    # ------------------------------------------------------------------
    # Build and return the complete audit dict
    # ------------------------------------------------------------------
    return {
        # ── Scoring trail ─────────────────────────────────────────────
        "base_score":            round(base_score,       4),
        "quality_bonus":         round(quality_bonus,    4),
        "vsa_adjustment":        round(vsa_adjustment,   4),
        "flag_adjustments":      round(flag_adj,         4),
        "weekly_cap_applied":    weekly_cap_applied,
        "macro_multiplier_used": macro_multiplier,
        "news_penalty_applied":  news_penalty,
        "final_score":           final_score,

        # ── Signal ────────────────────────────────────────────────────
        "signal_strength":       signal_strength,
        "direction":             direction_out,
        "position_size_pct":     position_size_pct,

        # ── Risk management ───────────────────────────────────────────
        "stop_loss":             round(stops_targets.get("stop_loss",  0.0), 4),
        "target_1":              round(stops_targets.get("target_1",   0.0), 4),
        "target_2":              round(stops_targets.get("target_2",   0.0), 4),
        "rr_ratio":              round(stops_targets.get("rr_ratio",   0.0), 4),
        "entry_zone":            _format_entry_zone(entry_timer.get("entry_zone")),

        # ── Context labels ────────────────────────────────────────────
        "vsa_flag":              vsa_flag,
        "weekly_gate_summary":   f"{weekly_gate_gate} | ADX {weekly_gate.get('adx_14', 0.0):.1f} ({adx_quality})",
        "atr_regime":            atr_label,
        "macro_regime":          macro_regime,

        # ── Human-readable audit trail ────────────────────────────────
        "reasons":               reasons,
    }


# ---------------------------------------------------------------------------
# Convenience loader
# ---------------------------------------------------------------------------

def load_combined_context(project_root: str = None) -> dict | None:
    """
    Loads shared/combined_context.json from the project root.
    Returns the parsed dict or None if missing / unreadable.
    """
    if project_root is None:
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
# __main__ — live 3-asset test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    from data_fetcher import fetch_all_assets
    from daily_signal import calculate_daily_signal
    from entry_timer  import check_entry
    from vsa_check    import run_vsa_check
    from levels       import calculate_atr_regime, calculate_key_levels, calculate_stops_and_targets

    # fetch_all_assets() keys on config.py asset["name"], not the ticker
    ASSETS = ["Gold", "SPX", "NQ"]
    LABEL  = {"Gold": "Gold (GLD/GC=F)", "SPX": "S&P 500 (SPY/^GSPC)", "NQ": "Nasdaq 100 (QQQ/^NDX)"}

    SEPARATOR = "-" * 62
    THICK_SEP  = "=" * 62

    print(THICK_SEP)
    print("  scorer.py  --  Live 3-Asset Final Score Test")
    print(THICK_SEP)

    # Try to load real combined_context for macro/news gates
    ctx = load_combined_context()
    if ctx:
        print("[*] combined_context.json loaded — macro + news gates active.")
    else:
        print("[!] combined_context.json not found — running without macro/news adjustments.")

    all_data = fetch_all_assets()

    # Load or mock weekly gates
    wg_path = os.path.join(os.path.dirname(__file__), "outputs", "weekly_gate.json")
    if os.path.exists(wg_path):
        with open(wg_path, "r") as f:
            weekly_gates = json.load(f)
        print("[*] Weekly gates loaded from disk.\n")
    else:
        weekly_gates = {}
        print("[!] Weekly gate file not found — using BOTH_ALLOWED mock.\n")

    results = {}

    for asset in ASSETS:
        label = LABEL.get(asset, asset)
        dfs   = all_data.get(asset, {})

        print(f"\n{SEPARATOR}")
        print(f"  Asset: {label} ({asset})")
        print(f"{SEPARATOR}")

        df_d  = dfs.get("daily",  None)
        df_4h = dfs.get("4h",     None)
        df_w  = dfs.get("weekly", None)

        if df_d is None or (hasattr(df_d, "empty") and df_d.empty):
            print("  [SKIP] No daily data available.")
            continue

        wg = weekly_gates.get(asset, {"gate": "BOTH_ALLOWED", "score_cap": 10.0,
                                       "adx_14": 0.0, "adx_quality": "UNKNOWN"})

        # ── Daily signal ─────────────────────────────────────────────
        daily_res = calculate_daily_signal(df_d, wg)
        sig_dir   = daily_res.get("signal", "NO_SIGNAL")

        # Force LONG when NO_SIGNAL to exercise the full scoring path
        forced_dir = sig_dir
        if sig_dir == "NO_SIGNAL":
            daily_res["signal"] = "LONG"
            daily_res["factors"]["F1_Trend"]    = 1
            daily_res["factors"]["F2_Momentum"] = 1
            daily_res["total_score"]            = 3
            forced_dir = "LONG (FORCED for test)"

        # ── Levels & ATR ─────────────────────────────────────────────
        regime     = calculate_atr_regime(df_d)
        levels     = calculate_key_levels(df_d)

        # ── Entry Timer ──────────────────────────────────────────────
        if df_4h is not None and not (hasattr(df_4h, "empty") and df_4h.empty):
            entry = check_entry(df_4h, daily_res, levels, regime)
        else:
            # Mock an entry-confirmed result so scoring path runs
            entry = {
                "mode": "PULLBACK", "signal_direction": daily_res["signal"],
                "entry_confirmed": True,
                "entry_zone": [df_d["Close"].iloc[-1] * 0.998,
                               df_d["Close"].iloc[-1] * 1.002],
                "conditions": {
                    "cond_a_ema_touch":   True,
                    "cond_b_macd_turn":   True,
                    "cond_c_struct_prox": False,
                    "deeper_pullback":    False,
                }
            }

        # ── VSA check ────────────────────────────────────────────────
        vsa = run_vsa_check(df_d, daily_res["signal"])

        # ── Stops & targets ──────────────────────────────────────────
        entry_price = df_d["Close"].iloc[-1]
        ez = entry.get("entry_zone")
        if ez and len(ez) == 2:
            entry_price = (ez[0] + ez[1]) / 2.0

        stops = calculate_stops_and_targets(entry_price, daily_res["signal"], regime)

        # ── FINAL SCORE ──────────────────────────────────────────────
        score = calculate_final_score(
            daily_signal     = daily_res,
            entry_timer      = entry,
            vsa_check        = vsa,
            weekly_gate      = wg,
            stops_targets    = stops,
            atr_regime       = regime,
            combined_context = ctx,
        )

        results[asset] = score

        # ── Per-asset clean summary ──────────────────────────────────
        print(f"  Signal Direction : {forced_dir}")
        print(f"  Daily Factors    : {daily_res.get('factors', {})}")
        print()
        print(f"  -- Scoring Trail -----------------------------------------------")
        print(f"  base_score           : {score['base_score']}")
        print(f"  + quality_bonus      : {score['quality_bonus']}")
        print(f"  + vsa_adjustment     : {score['vsa_adjustment']}")
        print(f"  + flag_adjustments   : {score['flag_adjustments']}")
        print(f"  weekly_cap_applied   : {score['weekly_cap_applied']}")
        print(f"  x macro_multiplier   : {score['macro_multiplier_used']}")
        print(f"  + news_penalty       : {score['news_penalty_applied']}")
        print(f"  -------------------------------------------------------")
        print(f"  FINAL SCORE          : {score['final_score']}")
        print()
        print(f"  -- Signal ------------------------------------------------------")
        print(f"  signal_strength      : {score['signal_strength']}")
        print(f"  direction            : {score['direction']}")
        print(f"  position_size_pct    : {score['position_size_pct']}%")
        print()
        print(f"  -- Risk Management ---------------------------------------------")
        print(f"  entry_zone           : {score['entry_zone']}")
        print(f"  stop_loss            : {score['stop_loss']:.4f}")
        print(f"  target_1             : {score['target_1']:.4f}")
        print(f"  target_2             : {score['target_2']:.4f}")
        print(f"  rr_ratio             : {score['rr_ratio']:.2f}:1")
        print()
        print(f"  -- Context Labels ----------------------------------------------")
        print(f"  vsa_flag             : {score['vsa_flag']}")
        print(f"  weekly_gate_summary  : {score['weekly_gate_summary']}")
        print(f"  atr_regime           : {score['atr_regime']}")
        print(f"  macro_regime         : {score['macro_regime']}")
        print()
        print(f"  -- Reasons -----------------------------------------------------")
        for i, r in enumerate(score["reasons"], 1):
            print(f"  {i:>2}. {r}")

    print(f"\n{THICK_SEP}")
    print("  All assets processed.")
    print(THICK_SEP)
