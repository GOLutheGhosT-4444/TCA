import json
import os
import sys
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

# =========================================================
# 1. INITIALIZATION & AUTHENTICATION
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY environment variable missing in GitHub Secrets.")
    sys.exit(1)

client = genai.Client()
MODEL_NAME = "gemini-1.5-flash"

# =========================================================
# 2. MASTER PROMPT DESIGN (CLEAN NEWS + 5 BULLETS ONLY)
# =========================================================
def process_news_with_ai(title, raw_content):
    prompt = f"""
    You are a strict data extraction engine. Your job is to clean the raw news text and extract bullet points.
    
    CRITICAL RULES:
    1. cleaned_news: A single paragraph containing the cleaned, factual summary of the news. DO NOT add any extra information not present in the input.
    2. bullets: Exactly 5 sharp, factual bullet points extracted from the text.
    3. STRICTLY output raw JSON only, matching the exact schema below.

    Desired JSON Schema Format:
    {{
        "cleaned_news": "Single cleaned paragraph here",
        "bullets": [
            "• Point 1",
            "• Point 2",
            "• Point 3",
            "• Point 4",
            "• Point 5"
        ]
    }}

    Input Title: {title}
    Input Raw Text: {raw_content[:10000]}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                ),
            )
            
            return json.loads(response.text.strip())

        except APIError as e:
            print(f"      ⚠️ API Error (Attempt {attempt+1}): {e}")
            if e.code == 429:
                time.sleep(60)
                continue
            return None
        except Exception as e:
            print(f"      ⚠️ Parsing Error: {e}")
            return None
    return None

# =========================================================
# 3. MAIN EXECUTION PIPELINE
# =========================================================
def main():
    print("🚀 Starting Step 2: Clean News & Bullet Extractor...")

    if not os.path.exists("1.json"):
        print("❌ Error: '1.json' not found.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: '1.json' formatting is broken or corrupted.")
            return

    print(f"📊 Total raw articles found in 1.json: {len(raw_data)}")

    valid_news = []
    for item in raw_data:
        title = item.get('title', '').strip()
        content = item.get('content', '').strip()
        
        if title and len(content) > 10:
            valid_news.append(item)

    print(f"✅ Total valid articles left for AI after filtering: {len(valid_news)}")

    if not valid_news:
        print("⚠️ WARNING: No valid items to push to Gemini. Outputting empty array.")
        with open("detailed_points.json", "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        return

    target_news = valid_news[:10]
    master_output = []

    for idx, item in enumerate(target_news):
        title = item.get('title')
        content = item.get('content', '')
        
        print(f"⏳ [{idx+1}/{len(target_news)}] Cleaning & Extracting: {title[:45]}...")
        
        ai_data = process_news_with_ai(title, content)
        
        if ai_data:
            structured_item = {
                "id": idx + 1,
                "title": title,
                "date": item.get('date', time.strftime("%Y-%m-%d")),
                "category": item.get('category', 'General Current Affairs'),
                "cleaned_news": ai_data.get("cleaned_news"),
                "bullets": ai_data.get("bullets")
            }
            master_output.append(structured_item)
            print("   ✅ Cleaned and bullet points extracted successfully!")
        else:
            print("   ❌ AI structure failed or skipped.")

        if idx < len(target_news) - 1:
            time.sleep(15)

    # Naya file name yahan set kar diya gaya hai
    with open("detailed_points.json", "w", encoding="utf-8") as f:
        json.dump(master_output, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Process Complete! 'detailed_points.json' generated with {len(master_output)} items.")

if __name__ == "__main__":
    main()
