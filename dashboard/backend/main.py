# AlphaForge Backend v2.2 — internal endpoints active
# redeployed: 2026-04-21b
import os
import datetime
from typing import Any
from fastapi import FastAPI, Depends, HTTPException, status, Header, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import config
import database
import auth
import data
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AlphaForge Dashboard API")

# Add CORS Middleware to explicitly support the React/Vercel frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://alpha-forge-wheat.vercel.app",
        "https://alpha-forge-git-main-alphahedge.vercel.app",
        "https://alpha-forge-9j5r1h34n-alphahedge.vercel.app",
        "https://alpha-forge-kj2yaqx1j-alphahedge.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.on_event("startup")
async def startup_event():
    print("AlphaForge Dashboard API running")

    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "alphaforge_admin_default")
    admin_pass = admin_pass[:72]

    if database.get_user(admin_user):
        database.delete_user(admin_user)

    success = database.create_user(admin_user, admin_pass)
    if success:
        print(f"Admin user '{admin_user}' recreated on startup")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.post("/auth/reset-admin")
def reset_admin():
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "alphaforge_admin_default")
    admin_pass = admin_pass[:72]
    
    # Force delete if exists
    if database.get_user(admin_user):
        database.delete_user(admin_user)
        
    # Recreate from .env values
    success = database.create_user(admin_user, admin_pass)
    if success:
        return {"status": "ok", "message": f"Admin user '{admin_user}' reset successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to Recreate Admin user")

_VALID_BOTS = {"macro", "news", "technicals", "cot", "debate", "risk"}

@app.post("/internal/update/{bot_name}")
async def internal_update(
    bot_name: str,
    payload: dict[str, Any] = Body(...),
    x_internal_key: str = Header(...)
):
    expected = os.getenv("INTERNAL_SECRET", "")
    if not expected or x_internal_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    if bot_name not in _VALID_BOTS:
        raise HTTPException(status_code=404, detail=f"Unknown bot: {bot_name}")
    database.save_bot_output(bot_name, payload)
    data.invalidate_cache()
    return {"status": "ok", "bot": bot_name}

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = database.get_user(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    access_token = auth.create_access_token(username=user["username"])
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = auth.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = database.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # Filter secure data payload before dropping into front-end
    safe_user = dict(user)
    safe_user.pop("hashed_password", None)
    return safe_user

@app.get("/auth/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/api/overview")
async def get_overview(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    assets = payload.get("technicals", {}).get("assets", {})
    
    any_active_signals = False
    for a_data in assets.values():
        if isinstance(a_data, dict):
            fs = a_data.get("final_score", {})
            if fs.get("signal_strength", "NO_SIGNAL") != "NO_SIGNAL":
                any_active_signals = True
                break
                
    verd = payload.get("signals", {})
                
    return {
        "pipeline_status": payload.get("pipeline_status", {}),
        "last_run_time": payload.get("last_updated", "N/A"),
        "any_active_signals": any_active_signals,
        "combined_risk_level": payload.get("combined_risk_level", "UNKNOWN"),
        "final_direction": verd.get("final_direction", "N/A"),
        "final_conviction": verd.get("overall_conviction", "N/A")
    }

@app.get("/api/signals")
async def get_signals(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    assets = payload.get("technicals", {}).get("assets", {})
    results = {}
    for asset_name, a_data in assets.items():
        if not isinstance(a_data, dict): continue
        fs  = a_data.get("final_score",   {})
        st  = a_data.get("stops_targets", {})
        ds  = a_data.get("daily_signal",  {})
        et  = a_data.get("entry_timer",   {})
        results[asset_name] = {
            "ticker":         a_data.get("ticker", asset_name),
            "direction":      fs.get("direction",       "NO_SIGNAL"),
            "final_score":    fs.get("final_score",     0.0),
            "signal_strength": fs.get("signal_strength", "NO_SIGNAL"),
            "entry_zone":     et.get("entry_zone", []),
            "stop_loss":      st.get("stop_loss"),
            "target_1":       st.get("target_1"),
            "target_2":       st.get("target_2"),
            "rr_ratio":       st.get("rr_ratio"),
            "vsa_flag":       a_data.get("vsa_check", {}).get("vsa_flag", "NONE"),
            "weekly_gate":    a_data.get("weekly_gate", {}).get("gate", "N/A"),
            "atr_regime":     fs.get("atr_regime", "N/A"),
            "entry_mode":     et.get("mode", "WAIT"),
            "factors":        ds.get("factors", {}),
            "reasons":        fs.get("reasons", []),
        }
    return results

@app.get("/api/technicals")
async def get_technicals(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    assets_raw = payload.get("technicals", {}).get("assets", {})
    results = {}
    for name, a in assets_raw.items():
        if not isinstance(a, dict): continue
        fs  = a.get("final_score",   {})
        ds  = a.get("daily_signal",  {})
        et  = a.get("entry_timer",   {})
        vsa = a.get("vsa_check",     {})
        wg  = a.get("weekly_gate",   {})
        atr = a.get("atr_regime",    {})
        lvl = a.get("levels",        {})
        st  = a.get("stops_targets", {})
        results[name] = {
            "ticker":             a.get("ticker", name),
            "direction":          fs.get("direction",          "NO_SIGNAL"),
            "final_score":        fs.get("final_score",        0.0),
            "signal_strength":    fs.get("signal_strength",    "NO_SIGNAL"),
            "position_size_pct":  fs.get("position_size_pct",  0),
            "base_score":         fs.get("base_score",         0.0),
            "quality_bonus":      fs.get("quality_bonus",      0.0),
            "vsa_adjustment":     fs.get("vsa_adjustment",     0.0),
            "flag_adjustments":   fs.get("flag_adjustments",   0.0),
            "macro_multiplier":   fs.get("macro_multiplier_used", 1.0),
            "news_penalty":       fs.get("news_penalty_applied",  0.0),
            "weekly_cap_applied": fs.get("weekly_cap_applied", False),
            "reasons":            fs.get("reasons",            []),
            "factors":            ds.get("factors",            {}),
            "daily_signal_dir":   ds.get("signal",             "NO_SIGNAL"),
            "total_factor_score": ds.get("total_score",        0),
            "entry_zone":         et.get("entry_zone"),
            "entry_mode":         et.get("mode",               "N/A"),
            "entry_confirmed":    et.get("entry_confirmed",    False),
            "entry_conditions":   et.get("conditions",         {}),
            "vsa_flag":           vsa.get("vsa_flag",          "NONE"),
            "vsa_hard_cancel":    vsa.get("hard_cancel",       False),
            "vsa_score_adj":      vsa.get("score_adjustment",  0.0),
            "weekly_gate":        wg.get("gate",               "UNKNOWN"),
            "adx_quality":        wg.get("adx_quality",        "UNKNOWN"),
            "score_cap":          wg.get("score_cap",          10.0),
            "adx_14":             wg.get("adx_14",             0.0),
            "atr_regime":         fs.get("atr_regime",         "NORMAL_VOL"),
            "atr_14":             atr.get("atr_14",            0.0),
            "atr_percentile":     atr.get("atr_percentile",    50.0),
            "nearest_support":    lvl.get("nearest_support",   0.0),
            "nearest_resistance": lvl.get("nearest_resistance", 0.0),
            "stop_loss":          st.get("stop_loss"),
            "target_1":           st.get("target_1"),
            "target_2":           st.get("target_2"),
            "rr_ratio":           st.get("rr_ratio"),
        }
    return results

def _score_dir(score: float) -> str:
    if score > 0.1: return "BULLISH"
    if score < -0.1: return "BEARISH"
    return "NEUTRAL"

@app.get("/api/macro")
async def get_macro(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    macro = payload.get("macro", {})
    news = payload.get("news", {})

    if not isinstance(macro, dict): macro = {}
    if not isinstance(news, dict): news = {}

    sentiment_fields = [
        ("Fed Hawkishness", "fed_hawkishness"),
        ("Geopolitical Risk", "geopolitical_risk"),
        ("Earnings Tone", "earnings_tone"),
        ("Overall Sentiment", "overall_sentiment"),
        ("Gold Score", "gold_score"),
        ("SPX Score", "spx_score"),
        ("NQ Score", "nq_score"),
        ("DOW Score", "dow_score"),
        ("BTC Score", "btc_score"),
        ("ETH Score", "eth_score"),
        ("Oil Score", "oil_score"),
        ("EURUSD Score", "eurusd_score"),
        ("USDJPY Score", "usdjpy_score"),
        ("USDCAD Score", "usdcad_score"),
        ("Institutional Divergence", "institutional_divergence"),
    ]
    sentiment_scores = {
        label: {"score": float(news.get(field, 0.0)), "direction": _score_dir(float(news.get(field, 0.0)))}
        for label, field in sentiment_fields
    }

    return {
        "macro_regime": macro.get("regime", "UNKNOWN"),
        "hawk_dove_score": float(news.get("fed_hawkishness", 0.0)) * 5,
        "narrative_momentum": news.get("narrative_momentum", {}),
        "sentiment_scores": sentiment_scores,
        "narrative_text": macro.get("narrative_text", ""),
        "indicators": macro.get("individual_scores", {}),
        "total_score": macro.get("total_score", 0),
        "run_date": macro.get("run_date", ""),
    }

@app.get("/api/news")
async def get_news(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    news = payload.get("news", {})
    if not isinstance(news, dict): news = {}

    has_data = news.get("_status") == "OK"

    category_map = [
        ("Fed Policy",        "fed_hawkishness"),
        ("Inflation",         None),
        ("GDP / Growth",      None),
        ("Employment",        None),
        ("Geopolitics",       "geopolitical_risk"),
        ("Risk Appetite",     "overall_sentiment"),
        ("Earnings",          "earnings_tone"),
        ("Dollar Strength",   "institutional_divergence"),
        ("Commodity Demand",  "gold_score"),
    ]

    categories = {}
    for label, field in category_map:
        score = float(news.get(field, 0.0)) if (field and has_data) else 0.0
        categories[label] = {
            "score": score,
            "direction": _score_dir(score),
            "available": field is not None and has_data,
        }

    nm = news.get("narrative_momentum", {})
    if not isinstance(nm, dict): nm = {}

    return {
        "categories": categories,
        "contradiction_flag": news.get("contradiction_flag", False),
        "contradiction_reason": news.get("contradiction_reason", ""),
        "narrative_momentum": nm,
        "dominant_narrative": news.get("dominant_narrative", ""),
        "forward_event_risk": news.get("forward_event_risk", "UNKNOWN"),
        "top_3_headlines": news.get("top_3_headlines", []),
    }

@app.get("/api/cot")
async def get_cot(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    cot_raw = payload.get("cot", {})
    # COT bot wraps per-asset data under an "assets" key
    cot_assets = cot_raw.get("assets", {}) if isinstance(cot_raw, dict) else {}
    results = {}
    for k, v in cot_assets.items():
        if not isinstance(v, dict):
            continue
        results[k] = {
            "institutional_bias": v.get("institutional_bias", "N/A"),
            "positioning_extreme": v.get("positioning_extreme", False),
            "positioning_percentile": v.get("positioning_percentile", "N/A"),
            "crowding_risk": v.get("crowding_risk", "N/A")
        }
    return results

@app.get("/api/debate")
async def get_debate(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    verd = payload.get("signals", {})
    debt = payload.get("debate", {})
    return {
        "bull_case": verd.get("bull_case") or debt.get("bull_case", "N/A"),
        "bear_case": verd.get("bear_case") or debt.get("bear_case", "N/A"),
        "risk_case": verd.get("risk_case") or debt.get("risk_case", "N/A"),
        "synthesis": verd.get("synthesis", "N/A"),
        "conviction_score": verd.get("overall_conviction", 0),
        "final_direction": verd.get("final_direction", "N/A")
    }
