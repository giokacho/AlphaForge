# risk_engine.py
# =============================================================================
# AlphaForge — Risk Engine
#
# Entry point for the risk-engine module. Reads the debate-bot's final verdict
# from shared/final_verdict.json and exposes it to downstream position-sizing
# and execution logic.
#
# Run standalone:  python risk-engine/risk_engine.py
# =============================================================================

import os
import json

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE        = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
_VERDICT_PATH = os.path.join(_PROJECT_ROOT, "shared", "final_verdict.json")

# Keys that must be present for the verdict to be considered valid.
# 'assets' is injected by run_debate.py Step 4 from technicals_data.
REQUIRED_KEYS = ["final_direction", "overall_conviction", "assets"]


# ---------------------------------------------------------------------------
# load_verdict
# ---------------------------------------------------------------------------
def load_verdict(verdict_path: str = _VERDICT_PATH) -> dict:
    """
    Reads and validates shared/final_verdict.json.

    Raises
    ------
    FileNotFoundError
        If the verdict file does not exist. Run run_debate.py first.
    KeyError
        If any required key is missing from the verdict.
    ValueError
        If the file exists but is not valid JSON.

    Returns
    -------
    dict
        The full verdict dictionary as written by the debate-bot.
    """
    # -- 1. File existence --------------------------------------------------
    if not os.path.isfile(verdict_path):
        raise FileNotFoundError(
            f"[risk-engine] final_verdict.json not found at:\n"
            f"  {verdict_path}\n"
            f"  Run debate-bot/run_debate.py to generate it first."
        )

    # -- 2. Parse JSON -------------------------------------------------------
    try:
        with open(verdict_path, "r", encoding="utf-8") as f:
            verdict = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"[risk-engine] final_verdict.json exists but is not valid JSON.\n"
            f"  Error: {exc}"
        ) from exc

    # -- 3. Key validation ---------------------------------------------------
    missing = [k for k in REQUIRED_KEYS if k not in verdict]
    if missing:
        raise KeyError(
            f"[risk-engine] final_verdict.json is missing required key(s): "
            f"{missing}\n"
            f"  Found keys: {list(verdict.keys())}"
        )

    return verdict


# ---------------------------------------------------------------------------
# calculate_risk_pct
# ---------------------------------------------------------------------------
def calculate_risk_pct(conviction: int | float) -> float:
    """
    Maps a conviction score (0–10) to an account risk percentage.

    Rules
    -----
    conviction 0 or NEUTRAL  -> 0.0 %
    conviction 1 – 3         -> 0.5 %
    conviction 4 – 6         -> 1.0 %
    conviction 7 – 8         -> 1.5 %
    conviction 9 – 10        -> 2.0 %

    Parameters
    ----------
    conviction : int | float
        Score produced by the debate-bot (overall_conviction field).
        Pass 0 or the string 'NEUTRAL' to receive 0 % risk.

    Returns
    -------
    float
        Risk as a percentage of account equity (e.g. 1.5 means 1.5 %).
    """
    # Handle explicit NEUTRAL signal or string conviction values
    if isinstance(conviction, str):
        if conviction.upper() == "NEUTRAL":
            return 0.0
        try:
            conviction = float(conviction)
        except ValueError:
            return 0.0

    conviction = float(conviction)

    if conviction <= 0:
        return 0.0
    elif conviction <= 3:
        return 0.5
    elif conviction <= 6:
        return 1.0
    elif conviction <= 8:
        return 1.5
    else:   # 9 – 10
        return 2.0


# ---------------------------------------------------------------------------
# calculate_dollar_risk
# ---------------------------------------------------------------------------
def calculate_dollar_risk(account_size: float, conviction: int | float) -> float:
    """
    Returns the exact dollar amount to risk on a trade.

    Parameters
    ----------
    account_size : float
        Total account equity in dollars.
    conviction : int | float
        Debate-bot conviction score (0–10), or 'NEUTRAL'.

    Returns
    -------
    float
        Dollar risk amount (e.g. 1500.0 for $100k account at conviction 7).
    """
    risk_pct = calculate_risk_pct(conviction)
    return round(account_size * risk_pct / 100, 2)


# ---------------------------------------------------------------------------
# calculate_position_size
# ---------------------------------------------------------------------------

# Unit label per ticker — Gold futures trade in contracts; equities in shares.
_TICKER_UNITS: dict[str, str] = {
    "GC=F":   "contracts",
    "^GSPC":  "shares",
    "^NDX":   "shares",
}

def calculate_position_size(
    asset: str,
    dollar_risk: float,
    stops_targets: dict,
) -> dict:
    """
    Calculates position size for a single asset using the risk-per-trade
    approach: position_size = floor(dollar_risk / stop_distance).

    Stop distance is derived from stops_targets as:
        abs(entry_price - stop_loss)

    Parameters
    ----------
    asset : str
        Asset ticker symbol (e.g. 'GC=F', '^GSPC', '^NDX').
    dollar_risk : float
        Maximum dollar amount to risk on the trade (from calculate_dollar_risk).
    stops_targets : dict
        The stops_targets sub-dict from technicals_data for this asset.
        Expected keys: entry_price, stop_loss, target_1, target_2.

    Returns
    -------
    dict with keys:
        asset          - ticker symbol
        dollar_risk    - passed-in dollar risk
        stop_distance  - absolute price distance between entry and stop
        position_size  - whole-number units (floored), 0 if stop invalid
        unit           - 'contracts' (Gold) or 'shares' (SPX / NQ)
    """
    unit = _TICKER_UNITS.get(asset, "shares")

    entry_price = float(stops_targets.get("entry_price", 0.0))
    stop_loss   = float(stops_targets.get("stop_loss",   0.0))
    stop_distance = abs(entry_price - stop_loss)

    if stop_distance == 0.0:
        print(
            f"[risk-engine] WARNING: stop_distance is zero for {asset} "
            f"(entry={entry_price}, stop={stop_loss}). "
            f"Position size set to 0."
        )
        return {
            "asset":         asset,
            "dollar_risk":   dollar_risk,
            "stop_distance": 0.0,
            "position_size": 0,
            "unit":          unit,
        }

    position_size = int(dollar_risk / stop_distance)   # floor via int()

    return {
        "asset":         asset,
        "dollar_risk":   dollar_risk,
        "stop_distance": round(stop_distance, 4),
        "position_size": position_size,
        "unit":          unit,
    }


# ---------------------------------------------------------------------------
# generate_trade_sheet
# ---------------------------------------------------------------------------
def generate_trade_sheet(
    account_size: float,
    verdict_path: str   = _VERDICT_PATH,
    ctx_path:     str   = os.path.join(_PROJECT_ROOT, "shared", "combined_context.json"),
) -> dict:
    """
    Ties the full risk pipeline together into a single trade instruction sheet.

    Steps
    -----
    1. Load and validate final_verdict.json.
    2. Load technicals_data from combined_context.json.
    3. For each asset with an active signal (not NO_SIGNAL):
       - Calculate dollar_risk from overall_conviction.
       - Derive position_size from stop distance.
       - Pull entry_zone, stop_loss, target_1, target_2, rr_ratio.
    4. Accumulate total_risk_dollars and total_risk_pct.
    5. Persist to risk-engine/outputs/YYYY-MM-DD_trade_sheet.json.

    Parameters
    ----------
    account_size : float
        Total account equity in dollars.
    verdict_path : str
        Override path to final_verdict.json (default: shared/final_verdict.json).
    ctx_path : str
        Override path to combined_context.json.

    Returns
    -------
    dict
        The full trade_sheet dictionary (also saved to disk).
    """
    import datetime

    # -- 1. Load verdict ----------------------------------------------------
    verdict    = load_verdict(verdict_path)
    conviction = verdict.get("overall_conviction", 0)
    direction  = verdict.get("final_direction", "NEUTRAL")
    timestamp  = verdict.get("run_timestamp",   "N/A")

    dollar_risk = calculate_dollar_risk(account_size, conviction)
    risk_pct    = calculate_risk_pct(conviction)

    # -- 2. Load technicals -------------------------------------------------
    tech_assets: dict = {}
    if os.path.isfile(ctx_path):
        try:
            with open(ctx_path, "r", encoding="utf-8") as f:
                ctx = json.load(f)
            tech_assets = ctx.get("technicals_data", {}).get("assets", {})
        except Exception as e:
            print(f"[risk-engine] WARNING: could not read combined_context.json — {e}")
    else:
        print(f"[risk-engine] WARNING: combined_context.json not found at {ctx_path}")

    # -- 3. Build per-asset entries (active signals only) ------------------
    per_asset: list[dict] = []
    total_risk_dollars    = 0.0

    for asset_name, a_data in tech_assets.items():
        ticker = a_data.get("ticker", "N/A")
        fs     = a_data.get("final_score",   {})
        st     = a_data.get("stops_targets", {})
        et     = a_data.get("entry_timer",   {})

        signal_strength = fs.get("signal_strength", "NO_SIGNAL")
        asset_direction = fs.get("direction",        "NO_SIGNAL")

        # Skip assets with no active signal
        if signal_strength in ["NO_SIGNAL", "NONE", "SYSTEM_FAILURE"] or asset_direction in ["NO_SIGNAL", "NONE", "SYSTEM_FAILURE"]:
            print(f"Skipping {asset_name} — no active signal.")
            continue

        # Position sizing
        pos = calculate_position_size(ticker, dollar_risk, st)

        # Entry zone: list [low, high] or None
        ez  = et.get("entry_zone")
        entry_zone_str = (
            f"{ez[0]:.4f}-{ez[1]:.4f}" if ez and len(ez) == 2 else "N/A"
        )

        asset_entry = {
            "asset":         asset_name,
            "ticker":        ticker,
            "direction":     asset_direction,
            "signal_strength": signal_strength,
            "conviction":    conviction,
            "position_size": pos["position_size"],
            "unit":          pos["unit"],
            "dollar_risk":   pos["dollar_risk"],
            "stop_distance": pos["stop_distance"],
            "entry_zone":    entry_zone_str,
            "stop_loss":     round(st.get("stop_loss",  0.0), 4),
            "target_1":      round(st.get("target_1",   0.0), 4),
            "target_2":      round(st.get("target_2",   0.0), 4),
            "rr_ratio":      round(st.get("rr_ratio",   0.0), 2),
        }

        per_asset.append(asset_entry)
        total_risk_dollars += dollar_risk

    total_risk_pct = round(total_risk_dollars / account_size * 100, 4) if account_size else 0.0

    # -- 4. Assemble trade sheet -------------------------------------------
    trade_sheet = {
        "generated_at":      datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "verdict_timestamp": timestamp,
        "account_size":      account_size,
        "overall_direction": direction,
        "overall_conviction": conviction,
        "total_risk_dollars": round(total_risk_dollars, 2),
        "total_risk_pct":    total_risk_pct,
        "active_trades":     len(per_asset),
        "per_asset":         per_asset,
    }

    # -- 5. Persist ---------------------------------------------------------
    output_dir = os.path.join(_HERE, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    date_str   = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out_path   = os.path.join(output_dir, f"{date_str}_trade_sheet.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(trade_sheet, f, indent=4)

    print(f"[risk-engine] Trade sheet saved -> {out_path}")
    return trade_sheet


# ---------------------------------------------------------------------------
# print_trade_sheet
# ---------------------------------------------------------------------------
def print_trade_sheet(trade_sheet: dict) -> None:
    """Prints a professional, human-readable trade instruction sheet."""
    print("=" * 60)
    print("                FINAL TRADE INSTRUCTIONS")
    print("=" * 60)
    print(f"  Account Size       : ${trade_sheet.get('account_size', 0):,.2f}")
    print(f"  Total Risk (USD)   : ${trade_sheet.get('total_risk_dollars', 0):,.2f}")
    print(f"  Total Risk (%)     : {trade_sheet.get('total_risk_pct', 0):.2f}%")
    print(f"  Overall Direction  : {trade_sheet.get('overall_direction', 'N/A')}")
    print(f"  Overall Conviction : {trade_sheet.get('overall_conviction', 0)}/10")
    print("-" * 60)
    
    per_asset = trade_sheet.get("per_asset", [])
    if not per_asset:
        print("  [No Active Trades Generated]")
        print("=" * 60)
        return
        
    for asset in per_asset:
        print(f"  ASSET: {asset.get('asset', 'N/A')} ({asset.get('ticker', 'N/A')})")
        print(f"    Direction     : {asset.get('direction', 'N/A')}")
        print(f"    Position Size : {asset.get('position_size', 0)} {asset.get('unit', '')}")
        print(f"    Entry Zone    : {asset.get('entry_zone', 'N/A')}")
        print(f"    Stop Loss     : {asset.get('stop_loss', 0.0):.4f}")
        print(f"    Target 1      : {asset.get('target_1', 0.0):.4f}")
        print(f"    Target 2      : {asset.get('target_2', 0.0):.4f}")
        print(f"    Risk/Reward   : {asset.get('rr_ratio', 0.0):.2f}")
        print("-" * 60)
    
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    SAMPLE_ACCOUNT = 100_000.0

    # -- Verdict loader section --------------------------------------------
    print("=" * 50)
    print("  RISK ENGINE -- Verdict Loader")
    print("=" * 50)

    try:
        verdict = load_verdict()
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"\n  ERROR: {e}")
        raise SystemExit(1)

    direction  = verdict.get("final_direction", "N/A")
    conviction = verdict.get("overall_conviction", 0)
    timestamp  = verdict.get("run_timestamp", "N/A")
    conflict   = verdict.get("conflict_warning", False)
    cancel     = verdict.get("hard_cancel_warning", False)

    risk_pct = calculate_risk_pct(conviction)
    dollar_risk = calculate_dollar_risk(SAMPLE_ACCOUNT, conviction)

    print(f"\n  Direction      : {direction}")
    print(f"  Conviction     : {conviction}")
    print(f"  Timestamp      : {timestamp}")
    print(f"  Conflict flag  : {conflict}")
    print(f"  Hard cancel    : {cancel}")
    print(f"  Risk %%         : {risk_pct:.1f}%%")
    print(f"  Dollar risk    : ${dollar_risk:,.2f}  (on ${SAMPLE_ACCOUNT:,.0f} account)")
    print("\n" + "=" * 50)
    print("  Verdict loaded successfully.")
    print("=" * 50)

    # -- Full conviction-level table ---------------------------------------
    print(f"\n{'=' * 50}")
    print(f"  CONVICTION -> RISK TABLE  (account: ${SAMPLE_ACCOUNT:,.0f})")
    print(f"{'=' * 50}")
    print(f"  {'Conviction':<12} {'Risk %%':<10} {'Dollar Risk':<14}")
    print(f"  {'-' * 36}")
    for c in range(0, 11):
        pct = calculate_risk_pct(c)
        usd = calculate_dollar_risk(SAMPLE_ACCOUNT, c)
        marker = "  <-- current" if c == int(conviction) else ""
        print(f"  {c:<12} {pct:<10.1f} ${usd:<13,.2f}{marker}")
    print(f"{'=' * 50}\n")

    # -- Generate Trade Sheet ----------------------------------------------
    try:
        sheet = generate_trade_sheet(SAMPLE_ACCOUNT)
        print("\n")
        print_trade_sheet(sheet)
    except Exception as e:
        print(f"  ERROR generating trade sheet: {e}")

    print(f"\n{'=' * 50}\n")
