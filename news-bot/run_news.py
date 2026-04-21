import os
import sys
import json
import traceback
import glob
import time
import schedule
import requests
from datetime import datetime
from filelock import FileLock, Timeout
from dotenv import load_dotenv

load_dotenv()

def post_to_backend(payload: dict) -> None:
    backend_url = os.getenv("ALPHAFORGE_BACKEND_URL", "http://localhost:8000")
    secret = os.getenv("INTERNAL_SECRET", "")
    try:
        resp = requests.post(
            f"{backend_url}/internal/update/news",
            json=payload,
            headers={"x-internal-key": secret},
            timeout=10
        )
        resp.raise_for_status()
        print(f"--> Backend POST /internal/update/news → {resp.status_code}")
    except Exception as e:
        print(f"--> Backend POST failed (non-fatal): {e}")

# Import local sub-modules dynamically to allow graceful failures
try:
    import fetcher_news
except ImportError:
    fetcher_news = None
try:
    import fetcher_alphavantage
except ImportError:
    fetcher_alphavantage = None
try:
    import fetcher_fed
except ImportError:
    fetcher_fed = None
try:
    import fetcher_fred
except ImportError:
    fetcher_fred = None
try:
    import weighter
except ImportError:
    weighter = None
try:
    import classifier
except ImportError:
    classifier = None
try:
    import hawk_dove_scorer
except ImportError:
    hawk_dove_scorer = None
try:
    import asset_scorer
except ImportError:
    asset_scorer = None
try:
    import velocity_detector
except ImportError:
    velocity_detector = None
try:
    import aggregator
except ImportError:
    aggregator = None


def export_for_orchestrator():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    news_outputs_dir = os.path.join(base_dir, "outputs")
    macro_reports_dir = os.path.join(project_root, "macro-bot", "reports")
    shared_dir = os.path.join(project_root, "shared")

    os.makedirs(shared_dir, exist_ok=True)

    # Read most recent news json
    news_files = glob.glob(os.path.join(news_outputs_dir, "*.json"))
    news_data = {}
    contradiction_flag = False
    forward_event_risk = "UNKNOWN"
    
    if news_files:
        latest_news = max(news_files, key=os.path.getmtime)
        try:
            with open(latest_news, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
                contradiction_flag = news_data.get('contradiction_flag', False)
                forward_event_risk = news_data.get('forward_event_risk', 'UNKNOWN')
        except Exception as e:
            print(f"Error reading news data: {e}")

    # Read most recent macro report
    macro_files = glob.glob(os.path.join(macro_reports_dir, "*.md"))
    macro_data = ""
    macro_regime = "UNKNOWN"
    
    if macro_files:
        latest_macro = max(macro_files, key=os.path.getmtime)
        try:
            with open(latest_macro, 'r', encoding='utf-8') as f:
                macro_data = f.read()
                upper_content = macro_data.upper()
                if "RISK_OFF" in upper_content or "RISK OFF" in upper_content:
                    macro_regime = "RISK_OFF"
                elif "RISK_ON" in upper_content or "RISK ON" in upper_content:
                    macro_regime = "RISK_ON"
                elif "TRANSITION" in upper_content:
                    macro_regime = "TRANSITION"
        except Exception as e:
            print(f"Error reading macro report: {e}")

    # Determine risk level
    if macro_regime == "RISK_OFF" or contradiction_flag or forward_event_risk == "HIGH":
        combined_risk_level = "HIGH"
    elif macro_regime == "TRANSITION":
        combined_risk_level = "MEDIUM"
    elif macro_regime == "RISK_ON" and not contradiction_flag and forward_event_risk == "LOW":
        combined_risk_level = "LOW"
    else:
        combined_risk_level = "MEDIUM"

    combined_context = {
        "macro_data": macro_data,
        "news_data": news_data,
        "system_date": datetime.now().strftime("%Y-%m-%d"),
        "combined_risk_level": combined_risk_level
    }

    out_file = os.path.join(shared_dir, "combined_context.json")
    lock_file = os.path.join(shared_dir, "combined_context.lock")
    try:
        with FileLock(lock_file, timeout=10):
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(combined_context, f, indent=4)
    except Timeout:
        raise TimeoutError("Could not acquire lock on combined_context.json within 10 seconds.")

    print(f"\n--- Orchestrator Export ---")
    print(f"Combined risk level: {combined_risk_level}")
    print(f"Context saved to {out_file}\n")
    return combined_risk_level

def run_once():
    now = datetime.now()
    start_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
    print(f"News Bot starting — {start_time_str}\n")
    
    # State holders to allow downstream steps to persist if earlier steps fail
    newsapi_articles = []
    alpha_articles = []
    fed_articles = []
    fred_data = {}
    combined_raw = []
    deduped = []
    classified = []
    hawk_scores = {}
    asset_scores = {}
    velocity_res = {}
    contradiction_results = {}
    alpha_avg = 0.0
    final_scores = {}
    
    # Step 1: NewsAPI
    try:
        if fetcher_news and hasattr(fetcher_news, 'fetch_newsapi'):
            newsapi_articles = fetcher_news.fetch_newsapi() or []
        print(f"Step 1 complete — {len(newsapi_articles)} articles fetched from NewsAPI")
    except Exception as e:
        print(f"Step 1 failed — NewsAPI fetching error: {e}")

    # Step 2: Alpha Vantage
    try:
        if fetcher_alphavantage and hasattr(fetcher_alphavantage, 'fetch_alphavantage'):
            alpha_articles = fetcher_alphavantage.fetch_alphavantage() or []
        
        valid_scores = [a.get('overall_sentiment_score') for a in alpha_articles if a.get('overall_sentiment_score') is not None]
        if valid_scores:
            alpha_avg = sum(valid_scores) / len(valid_scores)
            
        print(f"Step 2 complete — {len(alpha_articles)} articles fetched from Alpha Vantage")
    except Exception as e:
        print(f"Step 2 failed — Alpha Vantage fetching error: {e}")

    # Step 3: Fed and Reuters RSS
    try:
        if fetcher_fed and hasattr(fetcher_fed, 'fetch_fed_and_wires'):
            fed_articles = fetcher_fed.fetch_fed_and_wires() or []
        print(f"Step 3 complete — {len(fed_articles)} articles fetched from Fed/Reuters")
    except Exception as e:
        print(f"Step 3 failed — Fed/Reuters fetching error: {e}")

    # Step 4: FRED Event Risk
    try:
        if fetcher_fred and hasattr(fetcher_fred, 'fetch_event_risk'):
            fred_data = fetcher_fred.fetch_event_risk() or {}
        print(f"Step 4 complete — Event risk level is {fred_data.get('event_risk_level', 'Unknown')}")
    except Exception as e:
        print(f"Step 4 failed — FRED event risk fetching error: {e}")
        fred_data = {"event_risk_level": "UNKNOWN"}

    # Step 5: Weighter (Combine & Deduplicate)
    try:
        combined_raw = newsapi_articles + alpha_articles + fed_articles
        if weighter and hasattr(weighter, 'apply_source_weights'):
            weighted = weighter.apply_source_weights(combined_raw)
            deduped = weighter.deduplicate_articles(weighted)
        else:
            deduped = combined_raw
        print(f"Step 5 complete — {len(deduped)} total articles after deduplication")
    except Exception as e:
        print(f"Step 5 failed — Weighting/Deduplication error: {e}")
        deduped = newsapi_articles + alpha_articles + fed_articles

    # Step 6: Classifier
    try:
        if classifier and hasattr(classifier, 'classify_articles'):
            classified = classifier.classify_articles(deduped)
        else:
            classified = deduped
        print(f"Step 6 complete — Articles classified")
    except Exception as e:
        print(f"Step 6 failed — Classification error: {e}")
        classified = deduped

    # Step 7: Hawk/Dove Scorer
    try:
        if hawk_dove_scorer and hasattr(hawk_dove_scorer, 'score_fed_language'):
            hawk_scores = hawk_dove_scorer.score_fed_language(classified) or {}
        print(f"Step 7 complete — Fed language scored")
    except Exception as e:
        print(f"Step 7 failed — Hawk/Dove scoring error: {e}")

    # Step 8: Asset Scorer
    try:
        if asset_scorer and hasattr(asset_scorer, 'score_assets_and_narrative'):
            asset_scores = asset_scorer.score_assets_and_narrative(classified) or {}
        print(f"Step 8 complete — Assets scored")
    except Exception as e:
        print(f"Step 8 failed — Asset scoring error: {e}")

    # Step 9: Velocity Detector
    try:
        if velocity_detector:
            velocity_res = velocity_detector.track_narrative_velocity(asset_scores)
            
            # Sub-try block for the macro-bot extraction helper natively linked
            regime = "UNKNOWN"
            try:
                regime = velocity_detector.fetch_last_macro_regime()
            except Exception:
                pass
                
            hawk_val = hawk_scores.get('hawkishness_score', 0.0)
            flag, triggers, explanation = velocity_detector.detect_contradictions(asset_scores, hawk_val, regime)
            contradiction_results = {"flag": flag, "triggers": triggers, "explanation": explanation}
        print(f"Step 9 complete — Velocity and contradictions checked")
    except Exception as e:
        print(f"Step 9 failed — Velocity detection error: {e}")

    # Step 10: Aggregator
    try:
        if aggregator and hasattr(aggregator, 'aggregate_final_sentiment'):
            final_scores = aggregator.aggregate_final_sentiment(
                asset_results=asset_scores,
                hawk_results=hawk_scores,
                velocity_results=velocity_res,
                contradiction_results=contradiction_results,
                fred_results=fred_data,
                alpha_vantage_average=alpha_avg
            )
            aggregator.save_news_output(final_scores)
        print(f"Step 10 complete — Output aggregated and saved")
    except Exception as e:
        print(f"Step 10 failed — Aggregation error: {e}")
        
    print("\n=== FINAL SCORES ===")
    print(json.dumps(final_scores, indent=4))
    
    # Path Resolution Reporting
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs", f"{now.strftime('%Y-%m-%d')}_news_scores.json"))
    print(f"\nNews Bot complete — output saved to {output_path}")
    
    # Export combined context for the orchestrator
    combined_risk_level = export_for_orchestrator()

    # POST to Railway backend (local file save above is kept as backup)
    post_to_backend({**final_scores, "combined_risk_level": combined_risk_level or "UNKNOWN"})

if __name__ == '__main__':
    if "--now" in sys.argv:
        run_once()
    else:
        try:
            schedule.every().day.at("07:00", "America/New_York").do(run_once)
            schedule.every().day.at("16:30", "America/New_York").do(run_once)
        except Exception:
            # Fallback if current schedule library version lacks timezone argument support
            schedule.every().day.at("07:00").do(run_once)
            schedule.every().day.at("16:30").do(run_once)

        print('Scheduled — next runs at 7:00 AM and 4:30 PM ET')
        
        while True:
            schedule.run_pending()
            time.sleep(60)
