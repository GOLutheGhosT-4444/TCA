import json
import os
import sys
import time
import base64
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
# 2. SMART ENCRYPTION ENGINE (ONLY ENCRYPTS VALUES)
# =========================================================
EMOJI_CIPHER = {
    'A': '😀', 'B': '😃', 'C': '😄', 'D': '😁', 'E': '😆', 'F': '😅', 'G': '😂', 'H': '🤣',
    'I': '😊', 'J': '😇', 'K': '🙂', 'L': '🙃', 'M': '😉', 'N': '😌', 'O': '😍', 'P': '🥰',
    'Q': '😘', 'R': '😗', 'S': '😙', 'T': '😚', 'U': '😋', 'V': '😛', 'W': '😝', 'X': '😜',
    'Y': '🤪', 'Z': '🤨', 'a': '🧐', 'b': '🤓', 'c': '😎', 'd': '🥸', 'e': '🤩', 'f': '🥳',
    'g': '😏', 'h': '😒', 'i': '😞', 'j': '😔', 'k': '😟', 'l': '😕', 'm': '🙁', 'n': '☹️',
    'o': '😣', 'p': '😖', 'q': '😫', 'r': '😩', 's': '🥺', 't': '😢', 'u': '😭', 'v': '😤',
    'w': '😠', 'x': '😡', 'y': '🤬', 'z': '🤯', '0': '😳', '1': '🥵', '2': '🥶', '3': '😶',
    '4': '🫥', '5': '😐', '6': '😑', '7': '😬', '8': '🙄', '9': '😯', '+': '😦', '/': '😧',
    '=': '😮'
}

def encrypt_to_emojis(text_data):
    b64_bytes = base64.b64encode(text_data.encode('utf-8'))
    b64_string = b64_bytes.decode('utf-8')
    return "".join(EMOJI_CIPHER.get(char, char) for char in b64_string)

# 👉 Naya Function: Yeh sirf JSON ki values ko encrypt karega, keys aur structure ko nahi
def encrypt_json_values(data):
    if isinstance(data, dict):
        return {k: encrypt_json_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [encrypt_json_values(item) for item in data]
    elif isinstance(data, str):
        return encrypt_to_emojis(data)
    else:
        return data  # ID (numbers) waise hi rahenge

# =========================================================
# 3. MASTER AI EXTRACTOR
# =========================================================
def process_news_with_ai(title, raw_content):
    prompt = f"""
    You are an expert exam paper setter for competitive exams. Analyze the input title and text.
    Generate a JSON object strictly matching the schema below. Do not add external facts.

    CRITICAL SCHEMA:
    {{
        "cleaned_news": "Exactly ONE continuous paragraph summarizing the core news using ONLY input words.",
        "bullets": [
            "• Factual point 1",
            "• Factual point 2",
            "• Factual point 3",
            "• Factual point 4",
            "• Factual point 5"
        ],
        "vocabularies": [
            {{
                "word": "Target word from text",
                "meaning_en": "Simple English meaning",
                "meaning_hi": "Accurate Hindi meaning in Devanagari script",
                "synonyms": ["Syn1", "Syn2", "Syn3"],
                "antonyms": ["Ant1", "Ant2", "Ant3"]
            }}
        ],
        "english_booster": {{
            "error_spotting": {{
                "sentence": "Sentence modified to include a grammatical error.",
                "error": "The incorrect word",
                "correction": "The correct word",
                "rule": "Grammar rule explanation"
            }},
            "fill_in_the_blanks": {{
                "sentence": "A sentence from the text with a blank represented by _____",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "The correct option string"
            }},
            "rearrangement": {{
                "jumbled_parts": ["Part A text", "Part B text", "Part C text", "Part D text"],
                "correct_order": "ABCD"
            }}
        }}
    }}

    Input Title: {title}
    Input Raw Text: {raw_content[:10000]}
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
            )
            raw_output = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
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
# 4. MAIN PIPELINE
# =========================================================
def main():
    print(f"🚀 Initiating Pipeline using [{MODEL_NAME}]...")

    if not os.path.exists("1.json"):
        sys.exit(1)

    with open("1.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    valid_news = [item for item in raw_data if item.get('title') and len(item.get('content', '')) > 10][:10]
    
    if not valid_news:
        sys.exit(1)

    master_output = []

    for idx, item in enumerate(valid_news):
        print(f"⏳ [{idx+1}/{len(valid_news)}] Processing: {item.get('title')[:40]}...")
        ai_data = process_news_with_ai(item.get('title'), item.get('content', ''))
        
        if ai_data:
            structured_item = {
                "id": idx + 1,
                "title": item.get('title'),
                "date": item.get('date', time.strftime("%Y-%m-%d")),
                "category": item.get('category', 'General Current Affairs'),
                **ai_data
            }
            master_output.append(structured_item)
            print("   ✅ Compiled!")

        if idx < len(valid_news) - 1:
            time.sleep(15)

    if not master_output:
        sys.exit(1)

    print("🔒 Encrypting content values into custom emojis (Keeping JSON structure safe)...")
    
    # 👉 SMART ENCRYPTION: Sirf content encrypt hoga, structure nahi
    encrypted_master_output = encrypt_json_values(master_output)

    with open("detailed_points.json", "w", encoding="utf-8") as f:
        json.dump(encrypted_master_output, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 SUCCESS! Structured Encrypted data saved to 'detailed_points.json'.")

if __name__ == "__main__":
    main()