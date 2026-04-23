import json
import os
from datetime import datetime, timezone

def apply_hard_rules(synthesis_result: dict, all_no_signal: bool, high_uncertainty: bool, both_strong: bool, hard_cancel_present: bool, bear_result: dict = None, risk_result: dict = None):
    if bear_result is None:
        bear_result = synthesis_result.get('bear_result', {})
    if risk_result is None:
        risk_result = synthesis_result.get('risk_result', {})

    # Rule 1
    if all_no_signal and high_uncertainty:
        synthesis_result['final_direction'] = 'NEUTRAL'

    # Rule 2
    if synthesis_result.get('overall_conviction', 0) < 5:
        synthesis_result['final_direction'] = 'NEUTRAL'

    # Rule 3
    if both_strong:
        synthesis_result['position_size_recommendation'] = 'MINIMAL'
        synthesis_result['high_uncertainty_flag'] = True

    # Rule 4
    if hard_cancel_present and bear_result.get('conviction', 0) > 7:
        synthesis_result['hard_cancel_warning'] = True

    # Rule 5
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    file_path = os.path.join(project_root, 'shared', 'combined_context.json')

    conflict_warning = False
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                news_data = data.get('news_data', {})
                if news_data.get('contradiction_flag') is True:
                    conflict_warning = True
        except Exception as e:
            print(f"Error reading combined_context.json: {e}")

    if conflict_warning:
        synthesis_result['conflict_warning'] = True
    else:
        synthesis_result['conflict_warning'] = False

    # Add fields
    synthesis_result['regime_uncertainty'] = risk_result.get('regime_uncertainty', 'UNKNOWN')
    synthesis_result['run_timestamp'] = datetime.now(timezone.utc).isoformat()

    if 'high_uncertainty_flag' not in synthesis_result:
        synthesis_result['high_uncertainty_flag'] = False
    if 'hard_cancel_warning' not in synthesis_result:
        synthesis_result['hard_cancel_warning'] = False

    return synthesis_result

def run_synthesis(data_block=None, bull_result=None, bear_result=None, risk_result=None,
                  all_no_signal=False, high_uncertainty=False,
                  both_strong=False, hard_cancel_present=False):
    bull_r = bull_result if isinstance(bull_result, dict) else {}
    bear_r = bear_result if isinstance(bear_result, dict) else {}
    risk_r = risk_result if isinstance(risk_result, dict) else {}

    bull_conviction = bull_r.get("conviction", 5)
    bear_conviction = bear_r.get("conviction", 5)

    spread = bull_conviction - bear_conviction
    if spread >= 2:
        direction = "LONG"
        final_conviction = bull_conviction
    elif spread <= -2:
        direction = "SHORT"
        final_conviction = bear_conviction
    else:
        direction = "NEUTRAL"
        final_conviction = max(1, min(bull_conviction, bear_conviction) - 1)

    bull_case = bull_r.get("bull_summary", "N/A")
    bear_case = bear_r.get("bear_summary", "N/A")
    risk_case = (risk_r.get("top_tail_risk") or
                 bear_r.get("key_risk_to_bear_case") or "N/A")

    if bull_case != "N/A" and bear_case != "N/A":
        synthesis = (
            f"Bull thesis: {bull_case} "
            f"Bear thesis: {bear_case} "
            f"Key risk: {risk_case}"
        )
    else:
        synthesis = "N/A"

    synthesis_result = {
        "final_direction": direction,
        "overall_conviction": final_conviction,
        "position_size_recommendation": "NORMAL",
        "bull_case": bull_case,
        "bear_case": bear_case,
        "risk_case": risk_case,
        "synthesis": synthesis,
    }

    synthesis_result = apply_hard_rules(
        synthesis_result,
        all_no_signal=all_no_signal,
        high_uncertainty=high_uncertainty,
        both_strong=both_strong,
        hard_cancel_present=hard_cancel_present,
        bear_result=bear_r,
        risk_result=risk_r
    )
    return synthesis_result

if __name__ == "__main__":
    # Test execution printing complete final verdict
    test_verdict = run_synthesis(
        bull_result={"conviction": 8},
        bear_result={"conviction": 8},
        risk_result={"regime_uncertainty": "HIGH"},
        all_no_signal=False,
        high_uncertainty=False,
        both_strong=True,
        hard_cancel_present=True
    )

    print("Final Verdict:")
    print(json.dumps(test_verdict, indent=4))
