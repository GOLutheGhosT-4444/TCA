import json
import os
import sys
import time
import base64
from google import genai
from google.genai import types
from google.genai.errors import APIError

# =========================================================
# 1. INITIALIZATION & GITHUB SECRETS CHECK
# =========================================================
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY missing in GitHub Secrets.")
    sys.exit(1)

client = genai.Client()
MODEL_NAME = "gemini-1.5-flash"

# Unique 65-character map for Custom Emoji Encryption (Base64 characters to Emojis)
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
    """Converts plain text/json string into custom emoji encrypted format"""
    b64_bytes = base64.b64encode(text_data.encode('utf-8'))
    b64_string = b64_bytes.decode('utf-8')
    return "".join(EMOJI_CIPHER.get(char, char) for char in b64_string)

# =========================================================
# 2. MASTER ALL-IN-ONE PROMPT GENERATOR
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
            return json.loads(response.text.strip())
        except APIError as e:
            if e.code == 429:
                time.sleep(60)
                continue
            return None
        except Exception:
            return None
    return None

# =========================================================
# 3. MAIN PIPE SYSTEM
# =========================================================
def main():
    print("🚀 Initiating Supercharged Master AI Pipeline...")

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
        
        print(f"⏳ [{idx+1}/{len(target_news)}] AI Core Processing: {title[:40]}...")
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
            print("   ✅ Complete structural block compiled!")
        else:
            print("   ❌ Skip: AI processing failed for this entry.")

        if idx < len(target_news) - 1:
            time.sleep(15)

    if len(master_output) == 0:
        print("❌ CRITICAL: 0 blocks generated by AI. Execution stopped.")
        sys.exit(1)

    # Convert entire compiled data pack into JSON string
    final_json_string = json.dumps(master_output, ensure_ascii=False, indent=4)
    
    print("🔒 Encrypting database pack into emoji payloads...")
    emoji_ciphertext = encrypt_to_emojis(final_json_string)

    # Save secure payload wrapper into detailed_points.json
    secured_payload = {
        "status": "encrypted",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "payload": emoji_ciphertext
    }

    with open("detailed_points.json", "w", encoding="utf-8") as f:
        json.dump(secured_payload, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 SUCCESS! Secure encrypted data pack saved to 'detailed_points.json'.")

if __name__ == "__main__":
    main()