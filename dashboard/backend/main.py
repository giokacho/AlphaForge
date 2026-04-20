import os
import datetime
from fastapi import FastAPI, Depends, HTTPException, status
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
        "https://alpha-forge-9j5r1h34n-alphahedge.vercel.app"
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
        fs = a_data.get("final_score", {})
        st = a_data.get("stops_targets", {})
        results[asset_name] = {
            "direction": fs.get("direction", "NO_SIGNAL"),
            "final_score": fs.get("final_score", 0.0),
            "signal_strength": fs.get("signal_strength", "NO_SIGNAL"),
            "entry_zone": a_data.get("entry_timer", {}).get("entry_zone", []),
            "stop_loss": st.get("stop_loss"),
            "target_1": st.get("target_1"),
            "target_2": st.get("target_2"),
            "rr_ratio": st.get("rr_ratio"),
            "vsa_flag": a_data.get("vsa_check", {}).get("vsa_flag", "NONE"),
            "weekly_gate": a_data.get("weekly_gate", {}).get("direction", "N/A"),
            "atr_regime": a_data.get("atr_volatility", {}).get("regime", "N/A"),
            "entry_mode": a_data.get("entry_timer", {}).get("timer_state", "WAIT"),
            "factors": a_data.get("factors", {})
        }
    return results

@app.get("/api/macro")
async def get_macro(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    macro = payload.get("macro", {})
    news = payload.get("news", {})
    
    if not isinstance(macro, dict): macro = {}
    if not isinstance(news, dict): news = {}
    
    return {
        "macro_regime": macro.get("regime", "UNKNOWN"),
        "hawk_dove_score": news.get("hawk_dove_score", 0),
        "narrative_momentum": news.get("narrative_momentum", 0.0),
        "sentiment_scores": news.get("sentiment_scores", {})
    }

@app.get("/api/cot")
async def get_cot(current_user: dict = Depends(get_current_user)):
    payload = data.load_latest_data()
    cot_data = payload.get("cot", {})
    results = {}
    for k, v in cot_data.items():
        if k.startswith("_") or k == "run_timestamp" or not isinstance(v, dict):
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
