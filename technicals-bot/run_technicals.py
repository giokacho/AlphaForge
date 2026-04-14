# run_technicals.py
# =============================================================================
# AlphaForge — Technicals Bot Master Pipeline
#
# Orchestrates the full technical analysis pipeline across 3 assets.
# Each section (Setup, Weekly Gate, Daily Signal, etc.) is added as a
# numbered step in the main() function. This file is the single entry point
# for the technicals-bot module.
#
# Asset tickers (Yahoo Finance):
#   GC=F   — Gold Futures
#   ^GSPC  — S&P 500
#   ^NDX   — Nasdaq 100
# =============================================================================

import os
import csv
import json
import time
import glob
import datetime
import traceback
import pandas as pd
from filelock import FileLock, Timeout

# ---------------------------------------------------------------------------
# Module imports
# ---------------------------------------------------------------------------
from data_fetcher import fetch_all_assets, fetch_asset_data
from weekly_gate  import calculate_weekly_gate
from daily_signal import calculate_daily_signal
from levels       import calculate_atr_regime, calculate_key_levels, calculate_stops_and_targets
from entry_timer  import check_entry
from vsa_check    import run_vsa_check
from scorer       import calculate_final_score

# ---------------------------------------------------------------------------
# Asset definitions
# These map the 3 target tickers to human-readable labels used throughout
# the pipeline. Must stay consistent with config.py ASSETS list.
# ---------------------------------------------------------------------------
ASSETS = [
    {"ticker": "GC=F",  "name": "Gold"},
    {"ticker": "^GSPC", "name": "SPX"},
    {"ticker": "^NDX",  "name": "NQ"},
]

# Convenience lookup: name -> ticker and ticker -> name
NAME_TO_TICKER = {a["name"]:   a["ticker"] for a in ASSETS}
TICKER_TO_NAME = {a["ticker"]: a["name"]   for a in ASSETS}
ASSET_NAMES    = [a["name"] for a in ASSETS]   # ordered list for iteration


# ---------------------------------------------------------------------------
# Helper: load shared/combined_context.json
# ---------------------------------------------------------------------------
def _load_combined_context() -> dict | None:
    """
    Attempts to load shared/combined_context.json from the project root.
    Returns the parsed dict on success, None if the file is absent or corrupt.
    """
    base_dir     = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    ctx_path     = os.path.join(project_root, "shared", "combined_context.json")

    if not os.path.exists(ctx_path):
        print("[setup] shared/combined_context.json not found — "
              "macro/news gates will be skipped.")
        return None

    lock_path = ctx_path.replace(".json", ".lock")
    try:
        try:
            with FileLock(lock_path, timeout=10):
                with open(ctx_path, "r", encoding="utf-8") as f:
                    ctx = json.load(f)
        except Timeout:
            raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")
        print(f"[setup] combined_context.json loaded "
              f"(risk_level: {ctx.get('combined_risk_level', 'UNKNOWN')}).")
        return ctx
    except Exception as e:
        print(f"[setup] Warning: could not parse combined_context.json — {e}")
        return None



# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main() -> None:
    pipeline_start = time.time()
    now            = datetime.datetime.now()
    today_str      = now.strftime("%Y-%m-%d")
    timestamp_str  = now.strftime("%Y-%m-%d %H:%M:%S")

    base_dir   = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    wg_path = os.path.join(output_dir, "weekly_gate.json")

    print("=" * 56)
    print("  TECHNICALS BOT — MASTER PIPELINE")
    print(f"  Run started: {timestamp_str}")
    print("=" * 56)

    # Sentinel defaults — updated inside the try block.
    # Ensures the final summary can always print even if an early exception fires.
    active_signals = 0
    json_path      = "not saved"

    try:
        # ==================================================================
        # SETUP — Load combined context (macro + news gates)
        # ==================================================================
        print("\n[Step 0] Loading combined context...")
        combined_context = _load_combined_context()

        # ==================================================================
        # STEP 1 — Fetch all market data
        # ==================================================================
        print("\n[Step 1] Fetching market data for all assets...")
        all_data = fetch_all_assets()

        # Validate at least one asset returned data
        populated = {
            name: dfs for name, dfs in all_data.items()
            if "daily" in dfs and not dfs["daily"].empty
        }

        if not populated:
            print("[Step 1] ERROR: No asset data returned. "
                  "Check network connection and Yahoo Finance availability.")
            return

        fetch_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        asset_summary = ", ".join(
            f"{n} ({len(dfs['daily'])} bars)" for n, dfs in populated.items()
        )
        print(f"[Step 1] Data fetched successfully at {fetch_timestamp}")
        print(f"         Assets with daily data: {asset_summary}")

        # ==================================================================
        # STEP 2 — Weekly Gate
        # Runs every Monday (or on demand if the gate file is missing).
        # Result: weekly_gates dict keyed by asset name, matching all_data.
        # ==================================================================
        is_monday = datetime.date.today().weekday() == 0
        wg_path   = os.path.join(output_dir, "weekly_gate.json")

        def _calculate_and_save_gates(reason: str) -> dict:
            """Run calculate_weekly_gate for all assets and persist to disk."""
            print(f"[Step 2] {reason} — calculating weekly gates...")
            gates = {}
            for name, dfs in all_data.items():
                df_w = dfs.get("weekly", pd.DataFrame())
                if df_w.empty:
                    print(f"  [{name}] WARNING: No weekly data — using BOTH_ALLOWED fallback.")
                    gates[name] = {
                        "gate": "BOTH_ALLOWED", "adx_quality": "UNKNOWN",
                        "score_cap": 10.0, "adx_14": 0.0, "date": today_str
                    }
                    continue
                try:
                    wg = calculate_weekly_gate(df_w)
                    wg["date"] = today_str
                    gates[name] = wg
                except Exception as wg_err:
                    print(f"  [{name}] WARNING: Weekly gate calculation failed — {wg_err}")
                    gates[name] = {
                        "gate": "BOTH_ALLOWED", "adx_quality": "UNKNOWN",
                        "score_cap": 10.0, "adx_14": 0.0, "date": today_str
                    }

            with open(wg_path, "w", encoding="utf-8") as f:
                json.dump(gates, f, indent=4)
            print(f"[Step 2] Weekly gates saved to {wg_path}")
            return gates

        if is_monday:
            weekly_gates = _calculate_and_save_gates("Monday detected")
            wg_source = "CALCULATED (Monday)"
        elif not os.path.exists(wg_path):
            weekly_gates = _calculate_and_save_gates("No gate file found (fallback)")
            wg_source = "CALCULATED (fallback — file missing)"
        else:
            print("[Step 2] Not Monday — loading weekly gates from disk...")
            try:
                with open(wg_path, "r", encoding="utf-8") as f:
                    weekly_gates = json.load(f)
                wg_source = "LOADED from disk"
            except Exception as load_err:
                print(f"[Step 2] WARNING: Failed to load gate file ({load_err}) — recalculating.")
                weekly_gates = _calculate_and_save_gates("Load failure fallback")
                wg_source = "CALCULATED (fallback — load error)"

        # Print per-asset summary
        print(f"\n[Step 2] Source: {wg_source}")
        print(f"{'Asset':<10} {'Gate':<16} {'ADX':>7} {'ADX Quality':<14} {'Score Cap':>10}")
        print("-" * 62)
        for name in ASSET_NAMES:
            wg = weekly_gates.get(name, {})
            print(
                f"{name:<10} "
                f"{wg.get('gate', 'N/A'):<16} "
                f"{wg.get('adx_14', 0.0):>7.2f} "
                f"{wg.get('adx_quality', 'N/A'):<14} "
                f"{wg.get('score_cap', 0.0):>10.1f}"
            )

        # ==================================================================
        # STEPS 3–8 — Per-asset signal pipeline
        # Each asset is individually try/excepted so one failure cannot
        # prevent the remaining assets from being evaluated.
        # Result: asset_results dict keyed by asset name.
        # ==================================================================
        print("\n[Steps 3-8] Running per-asset signal pipeline...")
        print("=" * 56)

        asset_results = {}   # name -> full result dict

        for name in ASSET_NAMES:
            print(f"\n  [{name}]")
            try:
                # Pull this asset's DataFrames
                dfs  = all_data.get(name, {})
                df_d = dfs.get("daily",  pd.DataFrame())
                df_4h = dfs.get("4h",   pd.DataFrame())

                if df_d.empty:
                    print(f"  [{name}] SKIP — no daily data available.")
                    continue

                # Retrieve this asset's weekly gate (defaulting safely)
                wg = weekly_gates.get(name, {
                    "gate": "BOTH_ALLOWED", "score_cap": 10.0,
                    "adx_14": 0.0, "adx_quality": "UNKNOWN"
                })

                # ------------------------------------------------------
                # Step 3 — Daily signal
                # ------------------------------------------------------
                print(f"  [{name}] Step 3: Daily signal...")
                daily_signal = calculate_daily_signal(df_d, wg)
                sig_dir      = daily_signal.get("signal", "NO_SIGNAL")
                tot_score    = daily_signal.get("total_score", 0)
                factors      = daily_signal.get("factors", {})
                print(
                    f"    Signal: {sig_dir:<12} "
                    f"Total score: {tot_score:+d}  "
                    f"F1:{factors.get('F1_Trend',0):+d} "
                    f"F2:{factors.get('F2_Momentum',0):+d} "
                    f"F3:{factors.get('F3_Volatility',0):+d} "
                    f"F4:{factors.get('F4_Volume',0):+d}"
                )

                # ------------------------------------------------------
                # Step 4 — ATR regime + key levels
                # ------------------------------------------------------
                print(f"  [{name}] Step 4: ATR regime & key levels...")
                atr_regime = calculate_atr_regime(df_d)
                levels     = calculate_key_levels(df_d)
                print(
                    f"    ATR: {atr_regime.get('atr_14', 0.0):.4f}  "
                    f"Pct: {atr_regime.get('atr_percentile', 0.0):.1f}%  "
                    f"Mult: x{atr_regime.get('atr_multiplier', 1.0):.1f}  "
                    f"Support: {levels.get('nearest_support', 0.0):.2f}  "
                    f"Resistance: {levels.get('nearest_resistance', 0.0):.2f}"
                )

                # ------------------------------------------------------
                # Step 5 — 4H entry timer
                # ------------------------------------------------------
                print(f"  [{name}] Step 5: Entry timer...")
                if df_4h.empty:
                    print(f"    WARNING: No 4H data — entry will not be confirmed.")
                entry = check_entry(df_4h, daily_signal, levels, atr_regime)
                ez    = entry.get("entry_zone")
                print(
                    f"    Mode: {entry.get('mode', 'N/A'):<12} "
                    f"Confirmed: {str(entry.get('entry_confirmed', False)):<6} "
                    f"Zone: {f'{ez[0]:.2f}-{ez[1]:.2f}' if ez else 'N/A'}"
                )

                # ------------------------------------------------------
                # Step 6 — VSA check
                # ------------------------------------------------------
                print(f"  [{name}] Step 6: VSA check...")
                vsa = run_vsa_check(df_d, sig_dir)
                print(
                    f"    Flag: {vsa.get('vsa_flag', 'NONE'):<24} "
                    f"Hard cancel: {str(vsa.get('hard_cancel', False)):<6} "
                    f"Adj: {vsa.get('score_adjustment', 0.0):+.1f}"
                )

                # ------------------------------------------------------
                # Step 7 — Stops & targets
                # Entry price = midpoint of entry zone if confirmed,
                # otherwise fall back to last daily close.
                # ------------------------------------------------------
                print(f"  [{name}] Step 7: Stops & targets...")
                entry_price = df_d["Close"].iloc[-1]
                if ez and len(ez) == 2:
                    entry_price = (ez[0] + ez[1]) / 2.0

                stops_targets = calculate_stops_and_targets(
                    entry_price, sig_dir, atr_regime
                )
                if stops_targets:
                    print(
                        f"    Entry: {stops_targets.get('entry_price', 0.0):.2f}  "
                        f"SL: {stops_targets.get('stop_loss', 0.0):.2f}  "
                        f"T1: {stops_targets.get('target_1', 0.0):.2f}  "
                        f"T2: {stops_targets.get('target_2', 0.0):.2f}  "
                        f"R:R {stops_targets.get('rr_ratio', 0.0):.2f}:1"
                    )
                else:
                    print(f"    Stops not calculated (signal is NO_SIGNAL).")
                    stops_targets = {}

                # ------------------------------------------------------
                # Step 8 — Final score
                # ------------------------------------------------------
                print(f"  [{name}] Step 8: Final score...")
                score = calculate_final_score(
                    daily_signal     = daily_signal,
                    entry_timer      = entry,
                    vsa_check        = vsa,
                    weekly_gate      = wg,
                    stops_targets    = stops_targets,
                    atr_regime       = atr_regime,
                    combined_context = combined_context,
                )
                print(
                    f"    Score: {score.get('final_score', 0.0):.2f}  "
                    f"Strength: {score.get('signal_strength', 'N/A'):<12} "
                    f"Size: {score.get('position_size_pct', 0)}%  "
                    f"Macro x{score.get('macro_multiplier_used', 1.0):.2f}  "
                    f"News: {score.get('news_penalty_applied', 0.0):+.1f}"
                )

                # Collect full result keyed by asset name
                asset_results[name] = {
                    "ticker":       NAME_TO_TICKER.get(name, name),
                    "weekly_gate":  wg,
                    "daily_signal": daily_signal,
                    "atr_regime":   atr_regime,
                    "levels":       levels,
                    "entry_timer":  entry,
                    "vsa_check":    vsa,
                    "stops_targets": stops_targets,
                    "final_score":  score,
                }

            except Exception as asset_err:
                print(f"  [{name}] ERROR — pipeline failed: {asset_err}")
                traceback.print_exc()
                # Record failure instead of silently dropping
                asset_results[name] = {
                    "ticker": NAME_TO_TICKER.get(name, name),
                    "final_score": {
                        "signal_strength": "SYSTEM_FAILURE",
                        "error": str(asset_err),
                        "direction": "NONE",
                        "position_size_pct": 0,
                        "final_score": 0.0
                    },
                    "daily_signal": {"signal": "NO_SIGNAL"}
                }
                # Continue to next asset — do not abort the whole run
                continue

        print(f"\n[Steps 3-8] Complete — {len(asset_results)}/3 assets processed.")

        # ==================================================================
        # STEP 9 — Save outputs
        # Build the master technicals_output JSON and append to CSV history.
        # ==================================================================
        print("\n[Step 9] Saving outputs...")

        # ── 9a: Determine any_signals flag ─────────────────────────────────
        any_signals = any(
            res.get("final_score", {}).get("signal_strength", "NO_SIGNAL") != "NO_SIGNAL"
            for res in asset_results.values()
        )

        # ── 9b: Build master output dict ───────────────────────────────────
        technicals_output = {
            "run_timestamp": now.isoformat(),
            "any_signals":   any_signals,
            "assets":        asset_results,
        }

        # ── 9c: Save dated JSON snapshot ───────────────────────────────────
        json_path = os.path.join(output_dir, f"{today_str}_technicals.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(technicals_output, f, indent=4, default=str)
        print(f"[Step 9] JSON saved  -> {json_path}")

        # ── 9d: Append per-asset rows to CSV history ────────────────────────
        CSV_COLUMNS = [
            "date", "asset", "signal", "final_score", "signal_strength",
            "position_size_pct", "entry_mode", "stop_loss", "target_1",
            "target_2", "rr_ratio", "vsa_flag", "macro_multiplier_used",
        ]
        csv_path   = os.path.join(output_dir, "technicals_history.csv")
        csv_exists = os.path.isfile(csv_path)

        with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
            if not csv_exists:
                writer.writeheader()   # First-ever write — create headers

            for name, res in asset_results.items():
                fs  = res.get("final_score",   {})
                st  = res.get("stops_targets", {})
                ds  = res.get("daily_signal",  {})
                et  = res.get("entry_timer",   {})
                vsa = res.get("vsa_check",     {})

                writer.writerow({
                    "date":                 today_str,
                    "asset":               name,
                    "signal":              ds.get("signal", "NO_SIGNAL"),
                    "final_score":         fs.get("final_score",         0.0),
                    "signal_strength":     fs.get("signal_strength",     "NO_SIGNAL"),
                    "position_size_pct":   fs.get("position_size_pct",   0),
                    "entry_mode":          et.get("mode",                 "N/A"),
                    "stop_loss":           round(st.get("stop_loss",     0.0), 4),
                    "target_1":            round(st.get("target_1",      0.0), 4),
                    "target_2":            round(st.get("target_2",      0.0), 4),
                    "rr_ratio":            round(st.get("rr_ratio",      0.0), 4),
                    "vsa_flag":            vsa.get("vsa_flag",           "NONE"),
                    "macro_multiplier_used": fs.get("macro_multiplier_used", 1.0),
                })

        print(f"[Step 9] CSV updated -> {csv_path}")
        print(f"         Rows written: {len(asset_results)}  |  any_signals: {any_signals}")

        # ==================================================================
        # STEP 10 — Clean summary
        # ==================================================================
        active_signals = sum(
            1 for res in asset_results.values()
            if res.get("final_score", {}).get("signal_strength", "NO_SIGNAL") != "NO_SIGNAL"
        )

        print("\n" + "=" * 56)
        print("  PIPELINE SUMMARY")
        print("=" * 56)

        for name in ASSET_NAMES:
            res = asset_results.get(name)
            if res is None:
                print(f"\n  {name}: SKIPPED (no data or pipeline error)")
                continue

            fs  = res.get("final_score",   {})
            st  = res.get("stops_targets", {})
            et  = res.get("entry_timer",   {})
            ds  = res.get("daily_signal",  {})

            sig    = ds.get("signal",               "NO_SIGNAL")
            score  = fs.get("final_score",           0.0)
            strength = fs.get("signal_strength",    "NO_SIGNAL")
            mode   = et.get("mode",                  "N/A")
            sl     = st.get("stop_loss",             0.0)
            t1     = st.get("target_1",              0.0)
            t2     = st.get("target_2",              0.0)
            ticker = res.get("ticker",               name)

            print(f"\n  {name} ({ticker})")
            print(f"  {'Signal direction':<22}: {sig}")
            print(f"  {'Final score':<22}: {score:.2f}")
            print(f"  {'Signal strength':<22}: {strength}")
            print(f"  {'Entry mode':<22}: {mode}")
            if sl or t1 or t2:
                print(f"  {'Stop loss':<22}: {sl:.4f}")
                print(f"  {'Target 1':<22}: {t1:.4f}")
                print(f"  {'Target 2':<22}: {t2:.4f}")
            else:
                print(f"  {'Stop / Targets':<22}: N/A (no active signal)")
            print("  " + "-" * 40)

    except Exception as e:
        print(f"\n[PIPELINE ERROR] Uncaught exception: {e}")
        traceback.print_exc()
        return

    pipeline_end  = time.time()
    total_runtime = pipeline_end - pipeline_start

    print(f"\n{'=' * 56}")
    print(f"  Runtime       : {total_runtime:.2f}s")
    print(f"  Active signals: {active_signals} / {len(ASSET_NAMES)}")
    print(f"  JSON output   : {json_path}")
    print(f"{'=' * 56}")

    # Export results to shared context for debate-bot and orchestrator
    export_for_orchestrator()


# ---------------------------------------------------------------------------
# Orchestrator export
# ---------------------------------------------------------------------------
def export_for_orchestrator() -> None:
    """
    Reads the most recently written technicals JSON from outputs/,
    injects it as 'technicals_data' into shared/combined_context.json,
    updates combined_risk_level using priority-ordered rules, then
    writes the file back.

    Risk-level priority order:
      1. Any asset STRONG + macro RISK_ON  -> HIGH_OPPORTUNITY
      2. Any hard_cancel=True or news contradiction_flag=True -> ELEVATED_RISK
      3. All 3 assets NO_SIGNAL            -> LOW_ACTIVITY
      4. Otherwise keep existing value     -> default LOW_ACTIVITY if absent

    Called automatically at the end of main() so every pipeline run
    keeps the debate-bot fed with fresh data.
    """
    base_dir     = os.path.dirname(os.path.abspath(__file__))
    output_dir   = os.path.join(base_dir, "outputs")
    project_root = os.path.dirname(base_dir)
    shared_dir   = os.path.join(project_root, "shared")
    ctx_path     = os.path.join(shared_dir, "combined_context.json")

    # -- Step 1: find the most recent technicals JSON ----------------------
    tech_files = glob.glob(os.path.join(output_dir, "*_technicals.json"))
    if not tech_files:
        print("[export] WARNING: No technicals JSON found in outputs/ — skipping export.")
        return

    latest_json = max(tech_files, key=os.path.getmtime)
    try:
        with open(latest_json, "r", encoding="utf-8") as f:
            technicals_data = json.load(f)
    except Exception as e:
        print(f"[export] ERROR: Could not read {latest_json} — {e}")
        return

    # -- Step 2: load existing combined_context or start fresh -------------
    lock_path = ctx_path.replace(".json", ".lock")
    combined_context = {}
    if os.path.exists(ctx_path):
        try:
            try:
                with FileLock(lock_path, timeout=10):
                    with open(ctx_path, "r", encoding="utf-8") as f:
                        combined_context = json.load(f)
            except Timeout:
                raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")
        except Exception as e:
            print(f"[export] WARNING: Could not parse combined_context.json ({e}) "
                  f"— starting with empty dict.")
            combined_context = {}

    # -- Step 3: inject technicals -----------------------------------------
    combined_context["technicals_data"] = technicals_data

    # -- Step 4: derive macro regime from macro_data -----------------------
    macro_regime = "UNKNOWN"
    macro_raw    = combined_context.get("macro_data", "")
    macro_text   = (
        json.dumps(macro_raw) if isinstance(macro_raw, dict) else str(macro_raw)
    ).upper()
    if "RISK_OFF" in macro_text:
        macro_regime = "RISK_OFF"
    elif "RISK_ON" in macro_text:
        macro_regime = "RISK_ON"
    elif "TRANSITION" in macro_text:
        macro_regime = "TRANSITION"

    # -- Step 5: evaluate per-asset signals --------------------------------
    any_strong      = False
    any_hard_cancel = False
    all_no_signal   = True   # assume True until proven otherwise
    system_alerts   = []

    assets = technicals_data.get("assets", {})
    for _name, asset_data in assets.items():
        fs  = asset_data.get("final_score",  {})
        vsa = asset_data.get("vsa_check",    {})
        ds  = asset_data.get("daily_signal", {})

        if fs.get("signal_strength") == "STRONG":
            any_strong = True
        if vsa.get("hard_cancel") is True:
            any_hard_cancel = True
        if ds.get("signal", "NO_SIGNAL") != "NO_SIGNAL":
            all_no_signal = False
            
        if fs.get("signal_strength") == "SYSTEM_FAILURE":
            err_msg = fs.get("error", "Unknown error")
            system_alerts.append(f"PIPELINE FAILURE for {_name}: {err_msg}. Data for this asset may be severely compromised or missing.")
            
    if system_alerts:
        combined_context["system_alerts"] = system_alerts

    # contradiction_flag lives in news_data (written by the news-bot)
    news_data         = combined_context.get("news_data", {})
    any_contradiction = bool(news_data.get("contradiction_flag", False))

    # -- Step 6: apply risk-level rules in priority order ------------------
    existing_risk = combined_context.get("combined_risk_level", None)

    if any_strong and macro_regime == "RISK_ON":
        new_risk = "HIGH_OPPORTUNITY"
    elif any_hard_cancel or any_contradiction:
        new_risk = "ELEVATED_RISK"
    elif all_no_signal:
        new_risk = "LOW_ACTIVITY"
    else:
        new_risk = existing_risk if existing_risk is not None else "LOW_ACTIVITY"

    combined_context["combined_risk_level"] = new_risk

    # -- Step 7: persist ---------------------------------------------------
    try:
        with FileLock(lock_path, timeout=10):
            with open(ctx_path, "w", encoding="utf-8") as f:
                json.dump(combined_context, f, indent=4, default=str)
    except Timeout:
        raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")

    print(f"[export] Shared context updated successfully.")
    print(f"[export] Path: {ctx_path}")
    print(f"[export] Source: {os.path.basename(latest_json)} "
          f"(timestamp: {technicals_data.get('run_timestamp', 'N/A')})")
    print(f"[export] combined_risk_level: {new_risk}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
