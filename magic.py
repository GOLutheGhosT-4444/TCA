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
    print("❌ CRITICAL ERROR: GEMINI_API_KEY environment variable missing in GitHub Secrets.")
    sys.exit(1)

genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-1.5-flash"

# =========================================================
# 2. MASTER PROMPT DESIGN (STRICT JSON OUTPUT)
# =========================================================
def process_news_with_ai(title, raw_content):
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Ultra-Strict Master Prompt engineering for multiple sections
    prompt = f"""
    You are a strict, zero-hallucination data extraction engine for competitive exams (SSC, Banking, Military).
    Analyze the provided input news title and raw text, then generate a JSON object matching the exact schema below.

    CRITICAL RULES:
    1. detailed_news: Must be strictly ONE single continuous paragraph summarizing the core factual news. DO NOT add any extra word, assumption, or external fact not present in the input text.
    2. bullets: Extract exactly 3 to 5 sharp, factual bullet points containing dates, names, or amounts from the text.
    3. vocabularies: Identify any challenging/important vocabulary words present in the input text. For each word, provide:
       - meaning_en: Simple English meaning.
       - meaning_hi: Accurate Hindi meaning (in Devanagari script).
       - synonyms: Exactly 3 standard synonyms in English.
       - antonyms: Exactly 3 standard antonyms in English.
    4. english_booster: Create an exam-style question based strictly on the sentence structure of the news:
       - error_spotting: Rephrase a sentence from the news to introduce a clear grammatical error (e.g., subject-verb disagreement). Provide the broken 'sentence', the 'error' word, the 'correction', and the grammar 'rule' violated.
    5. STRICTLY output raw JSON only. Do NOT wrap the response in markdown code blocks like ```json ... ```. No meta-commentary or extra text allowed.

    Desired JSON Schema Format:
    {{
        "detailed_news": "Single summarized paragraph string here",
        "bullets": [
            "• Bullet point 1",
            "• Bullet point 2",
            "• Bullet point 3"
        ],
        "vocabularies": [
            {{
                "word": "TargetWord",
                "meaning_en": "Meaning in English",
                "meaning_hi": "Meaning in Hindi",
                "synonyms": ["Syn1", "Syn2", "Syn3"],
                "antonyms": ["Ant1", "Ant2", "Ant3"]
            }}
        ],
        "english_booster": {{
            "error_spotting": {{
                "sentence": "The sentence with a grammatical error.",
                "error": "wrong_word",
                "correction": "right_word",
                "rule": "Explanation of the grammar rule."
            }}
        }}
    }}

    Input Title: {title}
    Input Raw Text: {raw_content[:10000]}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.0, # Complete factual response, zero imagination
                    response_mime_type="application/json" # Forces Gemini to return pure valid JSON
                )
            )
            
            # Clean accidental markdown if any
            clean_json_str = response.text.strip()
            if clean_json_str.startswith("```json"):
                clean_json_str = clean_json_str.replace("```json", "").replace("```", "").strip()
                
            return json.loads(clean_json_str)

        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"   ⚠️ Rate Limit Hit! Sleeping 60s before retry {attempt+1}/{max_retries}...")
                time.sleep(60)
                continue
            else:
                print(f"   ❌ Generation Error: {e}")
                return None
    return None

# =========================================================
# 3. MAIN EXECUTION PIPELINE
# =========================================================
def main():
    print("🚀 Starting Step 2: Master AI Extraction Engine...")

    if not os.path.exists("1.json"):
        print("❌ Error: '1.json' not found. Run scraper.py first.")
        return

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: '1.json' is corrupted.")
            return

    # Take top 10 fresh news to stay within optimum processing bandwidth
    target_news = raw_data[:10]
    master_output = []

    for idx, item in enumerate(target_news):
        title = item.get('title')
        content = item.get('content', '')
        
        print(f"⏳ [{idx+1}/{len(target_news)}] Extracting Master Sections: {title[:45]}...")
        
        ai_data = process_news_with_ai(title, content)
        
        if ai_data:
            structured_item = {
                "id": idx + 1,
                "title": title,
                "date": item.get('date', time.strftime("%Y-%m-%d")),
                "category": item.get('category', 'General Current Affairs'),
                "detailed_news": ai_data.get("detailed_news"),
                "bullets": ai_data.get("bullets"),
                "vocabularies": ai_data.get("vocabularies"),
                "english_booster": ai_data.get("english_booster")
            }
            master_output.append(structured_item)
            print("   ✅ Extracted successfully!")
        else:
            print("   ❌ Failed to process this item.")

        # 15 seconds cool-down delay for Gemini free tier compliance
        if idx < len(target_news) - 1:
            time.sleep(15)

    # Save everything into the final Master file 4.json
    with open("4.json", "w", encoding="utf-8") as f:
        json.dump(master_output, f, indent=4, ensure_ascii=False)

    print("\n🎉 Master Strike Success! '4.json' is fully generated with all sections.")

if __name__ == "__main__":
    main()
