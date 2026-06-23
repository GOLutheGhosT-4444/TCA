import json
import os
import sys
import time
import google.generativeai as genai

# =========================================================
# 1. INITIALIZATION & GITHUB SECRETS CHECK
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY environment variable missing.")
    print("Ensure it is set in GitHub Repository Secrets with exact capitalization.")
    sys.exit(1)

genai.configure(api_key=API_KEY)

def get_flash_model():
    """Returns the name of the preferred fast free model"""
    return "models/gemini-1.5-flash"

# =========================================================
# 2. ULTRA-STRICT AI CLEANING FUNCTION (ZERO HALLUCINATION)
# =========================================================
def clean_news_with_ai(model_name, title, raw_content):
    """Gemini ko strictly filter karne par majboor karta hai without adding extra words"""
    model = genai.GenerativeModel(model_name)
    
    # Ultra-Strict Prompt Engineering to lock Gemini's imagination
    prompt = f"""
    You are a strict factual data filter for competitive exams. Your job is to clean the raw scraped text.

    CRITICAL RULES:
    1. Output strictly a SINGLE continuous paragraph containing only the core factual news.
    2. DO NOT add any extra line, greeting, introduction, conclusion, or pleasantry (e.g., Do not say "Here is the cleaned news:").
    3. DO NOT generate multiple paragraphs. Combine the facts into exactly ONE paragraph.
    4. ZERO HALLUCINATION: Use ONLY the information and words present in the raw input text. Do NOT add any external facts, explanations, or assumptions.
    5. Ensure numbers, amounts, dates, acronyms, and names are preserved exactly as they are in the input.

    Input News Title: {title}
    Input Raw Text: {raw_content[:12000]}  # Token boundary safety
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.0, # Zero creativity for absolute factual mapping
                )
            )
            
            cleaned_text = response.text.strip()
            
            # Post-processing safety block to remove any accidental AI meta-commentary
            if cleaned_text.startswith("Here is") or cleaned_text.startswith("Cleaned text:"):
                cleaned_text = cleaned_text.split("\n", 1)[-1].strip()
                
            return cleaned_text

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                print(f"   ⚠️ Rate Limit Hit! Sleeping 60s before retry {attempt+1}/{max_retries}...")
                time.sleep(60)
                continue
            else:
                return f"API ERROR: {str(e)[:60]}"

    return "Processing Failed due to Quota Exceeded"

# =========================================================
# 3. CORE PROCESSING PIPELINE
# =========================================================
def main():
    print("🚀 Step 2: AI Strict Data Cleaning Engine Initiated...")

    if not os.path.exists("1.json"):
        print("❌ Error: '1.json' raw data file not found in the root directory.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: '1.json' is corrupted or invalid JSON format.")
            return

    # Filter out items that don't have titles or are too small
    valid_news = [item for item in raw_data if item.get('title') and len(item.get('content', '')) > 40]
    
    # Process latest 10 news items to stay under optimal free-tier limits
    target_news = valid_news[:10]
    processed_news = []

    model_name = get_flash_model()
    print(f"🤖 Connected via GitHub Secret Token to: {model_name}\n")

    for idx, item in enumerate(target_news):
        title = item.get('title')
        raw_content = item.get('content', '')
        
        print(f"⏳ [{idx+1}/{len(target_news)}] Cleaning Factual Data: {title[:45]}...")
        
        # Fire strict request
        clean_paragraph = clean_news_with_ai(model_name, title, raw_content)
        
        if "API ERROR" not in clean_paragraph and "Failed" not in clean_paragraph:
            # Structuring the exact output format
            cleaned_item = {
                "id": idx + 1,
                "title": title,
                "date": item.get('date', time.strftime("%Y-%m-%d")),
                "category": item.get('category', 'General Current Affairs'),
                "content": clean_paragraph # Exactly 1 strict factual paragraph
            }
            processed_news.append(cleaned_item)
            print(f"   ✅ Success")
        else:
            print(f"   ❌ Failed (Reason: {clean_paragraph})")

        # Free tier 15s cooling delay to respect Gemini's RPM limit
        if idx < len(target_news) - 1:
            time.sleep(15)

    # Output saved directly to detailed_news.json as requested
    with open("detailed_news.json", "w", encoding="utf-8") as f:
        json.dump(processed_news, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Done! 100% original factual summaries saved to 'detailed_news.json'.")

if __name__ == "__main__":
    main()
