import os
import datetime
from config import GEMINI_API_KEY

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def generate_report(macro_data, result):
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set in config.py.")
        return fallback_report(result)
        
    if not HAS_GENAI:
        print("Warning: google-genai library is not installed.")
        return fallback_report(result)

    print("Generating report via Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    system_prompt = "You are a senior macro analyst at a global macro hedge fund. You write sharp, direct morning briefings. No fluff. Hedge fund language only."
    
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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        report_text = response.text
    except Exception as e:
        print(f"Warning: Failed to generate report from Gemini API: {e}")
        return fallback_report(result)
        
    # Ensure reports directory exists
    os.makedirs('reports', exist_ok=True)
    
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    report_path = os.path.join('reports', f"{today_str}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
        
    print("\n" + "="*50)
    print(" DAILY MACRO BRIEFING ".center(50, "="))
    print("="*50 + "\n")
    print(report_text)
    print("\n" + "="*50)
    print(f"Report saved to: {report_path}")
    
    return result.get('regime')


def fallback_report(result):
    """
    Writes a fallback report if the Gemini API call fails.
    """
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
        
    print("\n" + "="*50)
    print(" MACRO FALLBACK REPORT ".center(50, "="))
    print("="*50 + "\n")
    print(fallback_text)
    print(f"Fallback report saved to: {report_path}")
    
    return result.get('regime')


if __name__ == "__main__":
    from data_fetcher import fetch_macro_data, calculate_net_liquidity
    from scorer import score_macro
    print("Fetching latest data...")
    m_data = fetch_macro_data()
    m_data = calculate_net_liquidity(m_data)
    
    print("Scoring data...")
    res = score_macro(m_data)
    generate_report(m_data, res)
