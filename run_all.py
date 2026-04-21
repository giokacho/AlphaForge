import os
import sys
import json
import time
import datetime
import subprocess
import logging
import schedule

# Force UTF-8 on Windows so bot output with Unicode characters (→, etc.) logs cleanly
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- Setup Logging ---
base_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(base_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)

date_str = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(logs_dir, f"{date_str}_run.log")

# Clear root handlers if resetting
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("alphaforge")

def print_log(msg):
    logger.info(msg)

def pre_flight_checks():
    print_log("=" * 60)
    print_log("  PRE-FLIGHT CHECKS")
    print_log("=" * 60)
    
    env_files = [
        "macro-bot/.env",
        "news-bot/.env",
        "debate-bot/.env"
    ]
    for rel_path in env_files:
        p = os.path.join(base_dir, rel_path)
        if not os.path.isfile(p):
            print_log(f"[FAIL] Missing file: {rel_path}")
            sys.exit(1)
        if os.path.getsize(p) == 0:
            print_log(f"[FAIL] Empty file: {rel_path}")
            sys.exit(1)
            
    print_log("[PASS] Environmental variables verified.")
    
    try:
        from filelock import FileLock, Timeout
        lock_path = os.path.join(base_dir, "shared", "combined_context.lock")
        with FileLock(lock_path, timeout=0.1):
            pass
        print_log("[PASS] shared/combined_context.json is un-locked.")
    except Exception as e:
        print_log(f"[FAIL] shared/combined_context.json is currently locked! Aborting.")
        sys.exit(1)
        
    gate_path = os.path.join(base_dir, "technicals-bot", "outputs", "weekly_gate.json")
    if not os.path.isfile(gate_path):
        print_log(f"[FAIL] Missing weekly_gate.json file. Run technicals-bot once first.")
        sys.exit(1)
        
    mtime = os.path.getmtime(gate_path)
    age_hours = (time.time() - mtime) / 3600.0
    if age_hours > 168:
        print_log(f"[FAIL] weekly_gate.json is strictly stale ({age_hours:.1f}h old). Max allowed is 168h.")
        sys.exit(1)
        
    print_log(f"[PASS] weekly_gate.json is fresh ({age_hours:.1f}h old).")
    print_log("All pre-flight checks passed.\n")

def run_pipeline():
    pre_flight_checks()
    
    print_log("=" * 60)
    print_log("  INITIALIZING ALPHAFORGE MASTER PIPELINE")
    print_log("=" * 60)
    
    py_exec = sys.executable
    
    scripts = [
        [py_exec, "macro-bot/run.py"],
        [py_exec, "news-bot/run_news.py", "--now"],
        [py_exec, "technicals-bot/run_technicals.py"],
        [py_exec, "cot-bot/run_cot.py"],
        [py_exec, "debate-bot/run_debate.py"],
        [py_exec, "risk-engine/risk_engine.py"]
    ]
    
    total_start_time = time.time()
    bot_runtimes = {}
    
    for command in scripts:
        display_name = " ".join(["python"] + command[1:])
        bot_runtimes[display_name] = 0.0
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print_log(f"\n[{now}] >> Starting: {display_name}")
        
        step_start_time = time.time()
        try:
            sub_env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', env=sub_env)
            for line in process.stdout:
                logger.info(line.rstrip('\n'))
            process.wait()
            ret_code = process.returncode
        except Exception as e:
            print_log(f"\n[ERROR] Exception encountered while trying to run {display_name}")
            print_log(f"Details: {e}")
            print_log("PIPELINE HALTED.")
            sys.exit(1)
            
        step_duration = time.time() - step_start_time
        bot_runtimes[display_name] = step_duration
        
        if ret_code != 0:
            print_log(f"\n[ERROR] Validation failed. {display_name} returned exit code {ret_code}")
            print_log("PIPELINE HALTED. Downstream bots have been aborted to protect data integrity.")
            sys.exit(ret_code)
            
        finish_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print_log(f"[{finish_now}] << Completed: {display_name} (Duration: {step_duration:.2f}s)")
        
    total_duration = time.time() - total_start_time
    
    combined_risk_level = "UNKNOWN"
    final_conviction = "N/A"
    direction = "N/A"
    
    try:
        with open(os.path.join(base_dir, "shared", "combined_context.json"), "r", encoding="utf-8") as f:
            ctx = json.load(f)
            combined_risk_level = ctx.get("combined_risk_level", "UNKNOWN")
    except Exception:
        pass
        
    try:
        with open(os.path.join(base_dir, "shared", "final_verdict.json"), "r", encoding="utf-8") as f:
            verd = json.load(f)
            final_conviction = verd.get("overall_conviction", "N/A")
            direction = verd.get("final_direction", "N/A")
    except Exception:
        pass

    print_log("\n" + "=" * 60)
    print_log("  RUNTIME SUMMARY")
    print_log("=" * 60)
    print_log(f"  Total pipeline elapsed time : {total_duration:.2f}s")
    for name, dur in bot_runtimes.items():
        print_log(f"  - {name:<35} : {dur:.2f}s")
        
    print_log(f"\n  Final Combined Risk Level   : {combined_risk_level}")
    print_log(f"  Final Conviction Score      : {final_conviction}")
    print_log(f"  Recommended Direction       : {direction}")
    print_log("=" * 60)

def start_scheduler():
    def run_if_weekday():
        if datetime.datetime.today().weekday() < 5:
            run_pipeline()
    
    try:
        schedule.every().day.at("09:45", "America/New_York").do(run_if_weekday)
    except Exception:
        schedule.every().day.at("09:45").do(run_if_weekday)
        
    print_log("AlphaForge pipeline scheduled for 9:45 AM ET daily")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if "--schedule" in sys.argv:
        start_scheduler()
    else:
        run_pipeline()
