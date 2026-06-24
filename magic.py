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

# =========================================================
# 2. DYNAMIC MODEL AUTOPILOT (THE BRAIN)
# =========================================================
def auto_select_model(client_instance):
    """API se active models ki list mangega aur sabse best select karega"""
    print("🔍 Scanning Google AI Servers for available models...")
    try:
        # API se saare models ki list fetch karna
        available_models = list(client_instance.models.list())
        
        # Un models ka naam nikalna jo text generation support karte hain
        model_names = [m.name.replace('models/', '') for m in available_models if 'generateContent' in getattr(m, 'supported_generation_methods', ['generateContent'])]
        
        print(f"   📡 Found {len(model_names)} active models on your API key.")
        
        # Hamari Priority List (Sabse naya model pehle try karega)
        priority_list = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-pro"]
        
        for preferred in priority_list:
            if any(preferred in name for name in model_names):
                print(f"   🎯 Auto-Selected Optimal Model: {preferred}")
                return preferred
                
        # Agar priority list ka koi na mile, toh pehla "flash" model utha lo (kyunki wo fast aur free tier friendly hota hai)
        for name in model_names:
            if "flash" in name:
                print(f"   🎯 Fallback to available flash model: {name}")
                return name
                
        # Last resort: Jo bhi pehla model mile wo utha lo
        print(f"   ⚠️ Preferred flash models not found. Using default: {model_names[0]}")
        return model_names[0]
        
    except Exception as e:
        # Agar scan fail ho jaye (due to API restrictions), toh default safe model return karo
        print(f"   ⚠️ Auto-scan failed ({e}). Forcing safe default: gemini-2.0-flash")
        return "gemini-2.0-flash"

# Yahan script khud best model decide karegi
MODEL_NAME = auto_select_model(client)

# =========================================================
# 3. ENCRYPTION ENGINE
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

# =========================================================
# 4. MASTER ALL-IN-ONE PROMPT
# =========================================================
def process_news_with_ai(title, raw_content):
    prompt = f"""
    You are an expert exam paper setter for competitive exams. Analyze the input title and text.
    Generate a JSON object strictly matching the schema below. Do not add external facts.

    CRITICAL SCHEMA:
    {{
        "cleaned_news": "Exactly ONE continuous paragraph summarizing the core news using ONLY input words.",
        "bullets": [
            "• Factual point 1 with dates/names/amounts",
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
            
            raw_output = response.text.strip()
            raw_output = raw_output.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            
            return json.loads(raw_output)

        except APIError as e:
            print(f"      ⚠️ API Error (Attempt {attempt+1}): {e}")
            if e.code == 429:
                time.sleep(60)
                continue
            return None
        except json.JSONDecodeError as e:
            print(f"      ⚠️ JSON Parsing Error: {e}")
            return None
        except Exception as e:
            print(f"      ⚠️ Unexpected Error: {e}")
            return None
    return None

# =========================================================
# 5. MAIN PIPELINE
# =========================================================
def main():
    print(f"🚀 Initiating Supercharged AI Pipeline using [{MODEL_NAME}]...")

    if not os.path.exists("1.json"):
        print("❌ CRITICAL: '1.json' is missing.")
        sys.exit(1)

    with open("1.json", "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            print("❌ CRITICAL: '1.json' data is corrupted.")
            sys.exit(1)

    valid_news = [item for item in raw_data if item.get('title') and len(item.get('content', '')) > 10]
    
    if not valid_news:
        print("❌ CRITICAL: No valid data found inside 1.json.")
        sys.exit(1)

    target_news = valid_news[:10]
    master_output = []

    for idx, item in enumerate(target_news):
        title = item.get('title')
        content = item.get('content', '')
        
        print(f"⏳ [{idx+1}/{len(target_news)}] Processing: {title[:40]}...")
        ai_data = process_news_with_ai(title, content)
        
        if ai_data:
            structured_item = {
                "id": idx + 1,
                "title": title,
                "date": item.get('date', time.strftime("%Y-%m-%d")),
                "category": item.get('category', 'General Current Affairs'),
                **ai_data
            }
            master_output.append(structured_item)
            print("   ✅ Compiled successfully!")
        else:
            print("   ❌ Skip: Processing failed.")

        if idx < len(target_news) - 1:
            time.sleep(15)

    if len(master_output) == 0:
        print("❌ CRITICAL: 0 blocks generated. Execution stopped.")
        sys.exit(1)

    final_json_string = json.dumps(master_output, ensure_ascii=False, indent=4)
    print("🔒 Encrypting database into custom emojis...")
    emoji_ciphertext = encrypt_to_emojis(final_json_string)

    secured_payload = {
        "status": "encrypted",
        "model_used": MODEL_NAME, # Taki tumhe pata chale kaunsa model chala
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "payload": emoji_ciphertext
    }

    with open("detailed_points.json", "w", encoding="utf-8") as f:
        json.dump(secured_payload, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 SUCCESS! Encrypted data saved. Master file generated.")

if __name__ == "__main__":
    main()