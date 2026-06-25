import json
import os
import sys
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

# =========================================================
# 1. INITIALIZATION & SECRETS CHECK
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY missing in GitHub Secrets.")
    sys.exit(1)

client = genai.Client()

def auto_select_model(client_instance):
    print("🔍 Scanning Google AI Servers for available models...")
    try:
        available_models = list(client_instance.models.list())
        model_names = [m.name.replace('models/', '') for m in available_models if 'generateContent' in getattr(m, 'supported_generation_methods', ['generateContent'])]

        priority_list = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        for preferred in priority_list:
            if any(preferred in name for name in model_names):
                print(f"   🎯 Auto-Selected Optimal Model: {preferred}")
                return preferred

        return model_names[0] if model_names else "gemini-2.0-flash"
    except Exception as e:
        print(f"   ⚠️ Auto-scan failed. Forcing safe default: gemini-2.0-flash")
        return "gemini-2.0-flash"

MODEL_NAME = auto_select_model(client)

# =========================================================
# 2. STRICT AI CLEANER (NO EXTERNAL FACTS)
# =========================================================
def clean_news_with_ai(title, raw_content):
    prompt = f"""
    You are a strict editor and paper setter for competitive exams (UPSC, SSC, Banking).
    Your task is to filter and clean the provided news text.

    RULE 1 (GATEKEEPER): If the news is about office tips, lifestyle, gossip, movies, or personal opinions, you MUST reject it.
    RULE 2 (STRICT CLEANER): If relevant, summarize it into a highly professional, factual paragraph suitable for current affairs. 
    CRITICAL RULE: Do NOT hallucinate or add a single external fact, name, date, or context that is not explicitly present in the input. Use ONLY the provided text.

    OUTPUT SCHEMA (JSON format):
    {{
        "rejected": true/false,
        "cleaned_news": "The strictly cleaned paragraph here, or an empty string if rejected."
    }}

    Input Title: {title}
    Input Text: {raw_content[:10000]}
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
            )
            raw_output = response.text.strip().removeprefix("```json").removeprefix("
```").removesuffix("```").strip()
            return json.loads(raw_output)
        except APIError as e:
            if e.code == 429:
                time.sleep(60)
                continue
            return None
        except Exception:
            return None
    return None

# =========================================================
# 3. MAIN PIPELINE
# =========================================================
def main():
    print(f"🚀 Initiating AI Cleaner Pipeline using [{MODEL_NAME}]...")

    if not os.path.exists("1.json"):
        print("❌ CRITICAL: '1.json' is missing.")
        sys.exit(1)

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ CRITICAL: '1.json' is corrupted.")
            sys.exit(1)

    valid_news = [item for item in raw_data if item.get('title') and len(item.get('content', '')) > 10]

    if not valid_news:
        print("❌ CRITICAL: No valid data found in 1.json.")
        sys.exit(1)

    cleaned_output = []

    for idx, item in enumerate(valid_news):
        title = item.get('title')
        content = item.get('content', '')
        
        print(f"⏳ [{idx+1}/{len(valid_news)}] Evaluating: {title[:40]}...")
        ai_data = clean_news_with_ai(title, content)

        if ai_data:
            if ai_data.get("rejected") is True:
                print("   🚫 Rejected: Not relevant for exams.")
            else:
                # Sirf exam-relevant data save hoga
                cleaned_item = {
                    "id": len(cleaned_output) + 1,
                    "title": title,
                    "date": item.get('date', time.strftime("%Y-%m-%d")),
                    "category": item.get('category', 'General Current Affairs'),
                    "content": ai_data.get("cleaned_news", content)  # Content replace ho gaya clean version se
                }
                cleaned_output.append(cleaned_item)
                print("   ✅ Cleaned & Approved!")

        if idx < len(valid_news) - 1:
            time.sleep(15)  # API rate limit bachane ke liye

    if not cleaned_output:
        print("⚠️ All news were rejected or processing failed. No output generated.")
        sys.exit(0)

    print(f"💾 Saving {len(cleaned_output)} cleaned articles...")

    # Nayi clean file save karna
    with open("cleaned_1.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_output, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 SUCCESS! Pure exam-ready data saved to 'cleaned_1.json'.")

if __name__ == "__main__":
    main()