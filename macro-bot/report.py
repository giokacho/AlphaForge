import os
import datetime
import requests
from config import OPENROUTER_API_KEY

_MODEL   = "google/gemini-2.0-flash-001"
_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

def generate_report(macro_data, result):
    system_prompt = (
        "You are a senior macro analyst at a global macro hedge fund. "
        "You write sharp, direct morning briefings. No fluff. Hedge fund language only."
    )
    user_prompt = f"""
Here are the latest macro indicators and their scoring verdict:

Raw Data:
{macro_data}

Scoring Profile:
{result['individual_scores']}

Total Score: {result['total_score']}
Regime Verdict: {result['regime']}

Based on the above, write a 250-word macro brief covering:
1. Current regime verdict
2. The 3 biggest drivers today
3. The main risk to the thesis
4. 2 specific tactical trade ideas with direction and rationale
"""

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=_HEADERS,
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        report_text = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Warning: Failed to generate report from OpenRouter: {e}")
        return fallback_report(result)

    os.makedirs('reports', exist_ok=True)
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    report_path = os.path.join('reports', f"{today_str}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print("\n" + "=" * 50)
    print(" DAILY MACRO BRIEFING ".center(50, "="))
    print("=" * 50 + "\n")
    print(report_text)
    print("\n" + "=" * 50)
    print(f"Report saved to: {report_path}")

    return report_text


def fallback_report(result):
    os.makedirs('reports', exist_ok=True)
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    report_path = os.path.join('reports', f"{today_str}.md")

    fallback_text = f"# Macro Fallback Report\n\n"
    fallback_text += f"**Regime Verdict:** {result['regime']}\n"
    fallback_text += f"**Total Score:** {result['total_score']}\n\n"
    fallback_text += f"**Indicator Scores:**\n"
    for k, v in result['individual_scores'].items():
        fallback_text += f"- {k}: {v}\n"
    if result.get('missing_indicators'):
        fallback_text += f"\n**Missing Indicators:** {', '.join(result['missing_indicators'])}\n"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(fallback_text)

    print("\n" + "=" * 50)
    print(" MACRO FALLBACK REPORT ".center(50, "="))
    print("=" * 50 + "\n")
    print(fallback_text)
    print(f"Fallback report saved to: {report_path}")

    return fallback_text


if __name__ == "__main__":
    from data_fetcher import fetch_macro_data, calculate_net_liquidity
    from scorer import score_macro
    print("Fetching latest data...")
    m_data = fetch_macro_data()
    m_data = calculate_net_liquidity(m_data)
    print("Scoring data...")
    res = score_macro(m_data)
    generate_report(m_data, res)
