import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        # Configurable model with fallback
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        print(f"DEBUG: Gemini AI initialized successfully using {model_name}.")
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
else:
    print("DEBUG: GEMINI_API_KEY not found in environment variables.")

def get_offline_workout(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal or "weight_loss" in goal or "Vazn tashlash" in goal:
        return f"""{header}

<b>Dushanba (Butun tana):</b>
1. Yugurish (15 daqiqa)
2. O‘tirib turish (Squats) - 3x15
3. Jim yotib gantel ko‘tarish - 3x12
4. Plank - 3x45 soniya

<b>Chorshanba (Kardio + Press):</b>
1. Arqon sakrash - 10 daqiqa
2. Velosiped mashqi (press) - 3x20
3. Burpee - 3x10
4. Oyoq ko‘tarish (turnikda) - 3x12

<b>Juma (Oyoq va Yelka):</b>
1. Zina mashqi (10 daqiqa)
2. Lunges (Odimlash) - 3x15
3. Yelka pressi - 3x12
4. Yon tomonga gantel ko‘tarish - 3x15
"""
    elif "Massa" in goal or "muscle_gain" in goal or "Vazn olish" in goal:
        return f"""{header}

<b>Dushanba (Ko‘krak va Triceps):</b>
1. Jim yotib shtanga ko‘tarish - 4x8-10
2. Brusda ishlash - 3xMax
3. Gantel bilan pulover - 3x12
4. Triceps blokda - 3x12

<b>Chorshanba (Orqa va Biceps):</b>
1. Turnikda tortilish - 3xMax
2. Shtanga tortish (belga) - 4x8-10
3. Biceps shtanga - 3x10
4. Hammer (bolg‘a) usuli - 3x12

<b>Juma (Oyoq va Yelka):</b>
1. Shtanga bilan o‘tirib turish - 4x8-10
2. Oyoq pressi - 3x12
3. Yelka pressi (shtanga) - 3x10
4. Trapetsiya (shrugs) - 3x15
"""
    else: # Sog'liq / Umumiy
        return f"""{header}

<b>Dushanba:</b>
1. Yengil yugurish - 10 daqiqa
2. O‘tirib turish - 3x12
3. Otjimaniya - 3x10
4. Press mashqi - 3x15

<b>Chorshanba:</b>
1. Tez yurish - 20 daqiqa
2. Turnikda osilish - 3x30 soniya
3. Planka - 3x30 soniya
4. Cho‘zilish mashqlari

<b>Juma:</b>
1. Velosiped yoki Ellips - 15 daqiqa
2. Yengil gantel mashqlari - 3x12
3. Bel mashqlari (Gipertenziya) - 3x12
4. Nafas mashqlari
"""

def get_offline_menu(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal or "weight_loss" in goal or "Vazn tashlash" in goal:
        return f"""{header}

<b>Nonushta:</b>
- 2 ta qaynatilgan tuxum
- Yarimta avokado yoki 10 ta bodom
- Ko‘k choy (shakarsiz)

<b>Tushlik:</b>
- 150g tovuq ko‘krak go‘shti (qaynatilgan)
- Grechka (yog‘siz)
- Karam va sabzi salati

<b>Kechki ovqat:</b>
- 150g baliq yoki tvorog
- Yashil sabzavotlar
- 1 stakan kefir
"""
    elif "Massa" in goal or "muscle_gain" in goal or "Vazn olish" in goal:
        return f"""{header}

<b>Nonushta:</b>
- 3 ta tuxum (qovurilgan)
- Suli yormasi (sut bilan, banan va asal qo‘shilgan)
- Tost non (pishloq bilan)

<b>Tushlik:</b>
- 200g mol go‘shti yoki tovuq
- Guruch yoki makaron
- Sabzavotli salat (zaytun moyi bilan)

<b>Kechki ovqat:</b>
- 150g baliq yoki tovuq
- Kartoshka pyure
- Tvorog (smetana bilan)
"""
    else:
        return f"""{header}

<b>Nonushta:</b>
- Suli yormasi (mevalar bilan)
- 1 ta qaynatilgan tuxum
- Choy yoki qahva

<b>Tushlik:</b>
- Tovuq sho‘rva
- 100g go‘sht va garnir
- Salat

<b>Kechki ovqat:</b>
- Yengil hazm bo‘ladigan taom (dimlama)
- Salat
- Olma yoki nok
"""

# Global Safety Settings
# Global Safety Settings (New SDK Format)
SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

# Models to try in order
# Primary: from Env (default 2.5-flash)
# Fallback: 1.5-flash (more stable/faster/cheaper)
MODELS_TO_TRY = []
primary = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MODELS_TO_TRY.append(primary)
if primary != "gemini-1.5-flash":
    MODELS_TO_TRY.append("gemini-1.5-flash")

def get_profile_key(profile):
    """Generates a cache key for deduplication."""
    age = int(profile.get('age', 25))
    age_band = f"{age // 5 * 5}-{(age // 5 * 5) + 4}"
    
    return f"{profile.get('gender')}|{profile.get('goal')}|{profile.get('activity_level')}|{profile.get('allergies')}|{age_band}|v6"

# Usage Stats
AI_USAGE_STATS = {
    "workout": 0,
    "meal": 0,
    "chat": 0,
    "vision": 0,
    "shopping": 0,
    "support": 0,
    "errors": 0,
    "total_requests": 0
}

def ask_gemini(system_prompt, user_prompt):
    """
    Centralized helper to call Gemini with model fallback.
    Returns plain text response or raises Exception.
    """
    global client
    
    if not client:
        if not GEMINI_API_KEY:
            raise Exception("API Key not found")
        client = genai.Client(api_key=GEMINI_API_KEY)

    # Combine system and user prompt
    full_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
    
    last_error = None
    
    for model_name in MODELS_TO_TRY:
        try:
            print(f"DEBUG: Attempting AI generation with model: {model_name}")
            
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    safety_settings=SAFETY_SETTINGS,
                    # timeout is handled differently in the new SDK or at client level
                )
            )
            
            if response.text:
                return response.text.strip()
            
        except Exception as e:
            print(f"DEBUG: Model {model_name} failed: {e}")
            last_error = e
            continue # Try next model
            
    # If all models fail
    print("ERROR: All AI models failed.")
    AI_USAGE_STATS["errors"] += 1
    raise last_error or Exception("All AI models failed")

def call_gemini(prompt):
    """Legacy wrapper for backward compatibility, redirects to ask_gemini"""
    try:
        return ask_gemini("You are a helpful assistant.", prompt)
    except Exception as e:
        print(f"DEBUG: call_gemini caught exception: {e}")
        return None

def ai_generate_workout(user_profile):
    """Generates a weekly workout plan using Gemini or fallback."""
    AI_USAGE_STATS["workout"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    prompt = f"""
Siz Telegram uchun qisqa, silliq, tushunarli mashq rejalari tuzadigan professional fitness trenerisiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {user_profile.get('goal')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik darajasi: {user_profile.get('activity_level', 'Belgilanmagan')}

🎯 Vazifa:
Foydalanuvchiga 7 kunlik mashq rejasi tuzing.

📌 FORMAT TALABLARI:
- JSON formatda qaytar. "schedule" array ichida 7 ta kun bo'lsin.
- Mashq kunlari (1, 3, 5-kunlar) va Dam olish kunlari (2, 4, 6, 7-kunlar) bo'lsin.
- Dam olish kunlari uchun "focus": "Dam olish (Rest)" deb yozilsin va "exercises": "Bugun to'liq tiklanish kuni..." kabi matn bo'lsin.
- Mashq kunlari uchun "focus": "Ko'krak", "Oyoq" kabi bo'lsin.
- Javob FAQAT JSON bo'lsin.

Example structure:
{
  "schedule": [
    { "day": 1, "focus": "Ko'krak", "exercises": "..." },
    { "day": 2, "focus": "Dam olish (Rest)", "exercises": "..." },
    ...
  ]
}
"""
    
    response_text = call_gemini(prompt)
    if response_text and len(response_text) > 50: # Ensure meaningful response
        return format_gemini_text(response_text, "🏋️‍♂️ Sizning Individual Mashq Rejangiz")
        
    print(f"DEBUG: AI failed or returned empty. Using fallback for user {user_profile.get('name')}")
    return get_offline_workout(user_profile)

def ai_generate_menu(user_profile):
    """Generates a weekly meal plan using Gemini or fallback."""
    AI_USAGE_STATS["meal"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    # Build allergy warning if present
    allergy_text = user_profile.get('allergies')
    allergy_section = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        allergy_section = f"\n\n⚠️ ⚠️ ⚠️ JUDA MUHIM ⚠️ ⚠️ ⚠️\nFoydalanuvchida {allergy_text} ga ALLERGIYA BOR!\nTavsiya qilingan ovatlarda BU MAHSULOTLAR BO'LMASLIGI KERAK!\nAlternativ mahsulotlar tavsiya qiling.\n"
    
    # Map goals to Uzbek
    goal_map = {
        "weight_loss": "Vazn tashlash",
        "muscle_gain": "Vazn olish",
        "health": "Sog'lomlikni saqlash"
    }
    default_goal = "Sog'lomlik"
    goal_uz = goal_map.get(user_profile.get('goal'), user_profile.get('goal', default_goal))
    
    activity_level = user_profile.get('activity_level', "O'rtacha")
    prompt = f"""
Siz professional dietolog va fitness murabbiysiz.
Vazifa: O'zbek tilida 1 KUNLIK professional ovqatlanish rejasi tuzing.

Foydalanuvchi ma'lumotlari:
- Maqsad: {goal_uz}
- Faollik: {activity_level}
- Yoshi: {user_profile.get('age')}
- Vazni: {user_profile.get('weight')} kg
{allergy_section}

O'QISH FORMATI (QAT'IY RIAOYA QILING):
Format buzulmasin. Jadval ishlatmang.

🍽 [X]-kun uchun sog'lom menyu — [XXXX] kcal

🥣 Nonushta: [Taom nomi va kkal]
• [Masalliqlar ro'yxati]
- Tayyorlanishi: [1-2 gapda aniq tushuntirish]
- ⏱ [Vaqt] | 💰 [Narx darajasi] | 🏠

🍎 Tamaddi: [Nomi va kkal]
• [Masalliq]
- Tayyorlanishi: [Qisqa yo'riqnoma]

🍛 Tushlik: [Taom nomi va kkal]
• [Masalliqlar]
- Tayyorlanishi: [Qisqa retsept]
- ⏱ [Vaqt] | 💰 [Narx] | 🍲

🥗 Kechki ovqat: [Taom nomi va kkal]
• [Masalliqlar]
- Tayyorlanishi: [Qisqa retsept]
- ⏱ [Vaqt] | 💰 [Narx] | 🌙

📊 Kun yakuni
- 🔥 Jami kcal: [XXXX]
- 🎯 Maqsad: {goal_uz} uchun mos
- ✅ [Qisqa xulosa 1 gap]

TALABLAR:
1. O'zbek tilida so'zlashuv uslubida, tushunarli yozing.
2. Tarkibida O'zbekistonda bor mahsulotlar bo'lsin.
3. Tayyorlash jarayoni juda qisqa va aniq bo'lsin.
4. AI haqida gapirmang, faqat reja.
5. 1 kunlik reja tuzing.
"""

    response_text = call_gemini(prompt)
    
    if response_text:
        print(f"DEBUG: AI Response Length: {len(response_text)}")
    else:
        print("DEBUG: AI Response was None or Empty.")

    if response_text and len(response_text) > 50:
        return format_gemini_text(response_text, "Sizning ovqatlanish rejangiz")

    print(f"DEBUG: AI failed validation (len > 50). Using fallback for user {user_profile.get('name')}")
    return get_offline_menu(user_profile)


MOCK_MENU_DATA = {
  "menu": [
    { "day": 1, "breakfast": "2 ta qaynatilgan tuxum, suli yormasi", "lunch": "Tovuq sho'rva, 1 tilim qora non", "dinner": "Dimlama (go'sht va sabzavotlar)", "snack": "1 ta olma" },
    { "day": 2, "breakfast": "Tvorog va smetana, ko'k choy", "lunch": "Moshkichiri, salat", "dinner": "Grill tovuq ko'krak qismi", "snack": "Bir hovuch yong'oq" },
    { "day": 3, "breakfast": "Omlet (2 tuxum, sut)", "lunch": "Mastava, qatiq", "dinner": "Baliq (duxovkada)", "snack": "Kefir" },
    { "day": 4, "breakfast": "Grechka sut bilan", "lunch": "Suyuq lag'mon", "dinner": "Sabzavotli salat va tovuq", "snack": "Apelsin" },
    { "day": 5, "breakfast": "Pishloqli buterbrod, kofe", "lunch": "No'xat shorva", "dinner": "Qaynatilgan mol go'shti, karam salat", "snack": "Quritilgan mevalar" }
  ],
  "shopping_list": [
    "Tuxum (10 dona)", "Tovuq go'shti (1 kg)", "Mol go'shti (0.5 kg)", "Baliq (0.5 kg)",
    "Suli yormasi", "Grechka", "Guruch", "Mosh",
    "Sabzavotlar (Kartoshka, Piyoz, Sabzi, Karam)", "Mevalar (Olma, Apelsin)",
    "Sut mahsulotlari (Tvorog, Smetana, Kefir, Sut)", "Non"
  ]
}

def ai_generate_monthly_menu_json(user_profile):
    """Generates a 30-day structured meal plan + shopping list in JSON."""
    AI_USAGE_STATS["meal"] += 1
    AI_USAGE_STATS["total_requests"] += 1

    # 0. CACHE CHECK
    from core.db import db
    import json
    
    profile_key = get_profile_key(user_profile)
    cached = db.get_menu_template(profile_key)
    
    if cached:
        print(f"DEBUG: Cache Hit for Menu: {profile_key}")
        try:
             return {
                 "menu": json.loads(cached['menu_json']),
                 "shopping_list": json.loads(cached['shopping_list_json'])
             }
        except Exception as e:
             print(f"Cache Corrupt: {e}")

    allergy_text = user_profile.get('allergies')
    allergy_section = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        allergy_section = f"DIQQAT: Foydalanuvchida {allergy_text} ga allergiya bor. Menyuda bular qat'iyan bo'lmasin!"

    
    
    
    # 1. System Prompt (Rich Nutritional Role)
    # 1. System Prompt (Rich Nutritional Role - UPDATED STRICT)
    system_prompt = """
You are a professional Uzbek nutritionist, home chef, and supportive fitness coach.

Your task is to generate a 7-day meal plan in STRICT JSON format.

CONTEXT:
- Diet style: Oddiy o‘zbek uy ovqatlari
- Budget: Arzon / O‘rtacha
- Ingredients must be easily available in Uzbekistan
- Cooking skill: Boshlang‘ich
- Tone: Iliq, qo‘llab-quvvatlovchi, murabbiyona (insondek)

CRITICAL RULES (VERY IMPORTANT):

1. OUTPUT MUST BE VALID JSON ONLY. NO TEXT OUTSIDE JSON.
2. JSON STRUCTURE MUST NEVER CHANGE.
3. LANGUAGE: FAQAT O‘ZBEK TILI. HECH QANDAY INGLIZCHA SO‘Z YO‘Q (Values must be Uzbek, but JSON Keys must be English matching the schema).
4. USERGA DOIM "SIZ" DEB MUROJAAT QILING.

CALORIE RULES (STRICT):
- DAILY_TOTAL_KCAL MUST BE BETWEEN 1400 AND 1500 (Adjust steps/ingredients to fit).
- EVERY MEAL MUST HAVE 'kcal' (INTEGER).
- DAILY kcal MUST BE LOGICALLY DISTRIBUTED:
  - Nonushta: 25–30%
  - Tushlik: 35–40%
  - Kechki ovqat: 20–25%
  - Tamaddi: 5–10%
- If kcal does NOT fit → YOU MUST FIX IT.

MEAL STRUCTURE (DO NOT CHANGE):
Each meal object MUST include:
- title (string)
- ingredients (array of strings WITH QUANTITIES)
- preparation_steps (array of strings, step-by-step)
- time_minutes (integer)
- cost_level ('Arzon' | 'O\'rtacha' | 'Qimmat')
- place ('uy')
- kcal (integer)

SNACK (TAMADDI):
- MUST be an OBJECT
- title MUST be very short (2–3 words)
- kcal is REQUIRED

SHOPPING LIST:
- MUST be an OBJECT
- GROUPED BY CATEGORIES: 'protein', 'veg', 'carbs', 'dairy', 'misc'
- Quantities MUST be TOTAL for 7 DAYS (Masalan: "Tovuq filesi — 1.5 kg")

DAILY OBJECT MUST INCLUDE:
- day (integer, 1-7)
- day_name (string, e.g. "Dushanba")
- breakfast, lunch, dinner, snack
- total_kcal (integer)
- micro_advice (1–2 short motivating sentences)

"""

    # 2. User Prompt (Data)
    if 'allergies' in user_profile and user_profile['allergies']:
         allergy_info = user_profile['allergies']
    else:
         allergy_info = "yo‘q"

    user_prompt = f"""
🔹 USER PROMPT (DYNAMIC)

Ma'lumotlar:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik: {user_profile.get('activity_level', 'O’rtacha')}
Maqsad: {user_profile.get('goal', 'Vazn yo‘qotish')}
Allergiya: {allergy_info}

Talablar:
- 7 kunlik menyu
- Ovqatlar uy sharoitida tayyorlanadigan bo‘lsin
- Mahsulotlar arzon va topilishi oson bo‘lsin
- Har kun yakunida aniq kaloriya chiqsin
- Foydalanuvchini ruhlantiruvchi micro_advice bo‘lsin
"""

    
    # 3. Model Configuration
    model_name = 'gemini-2.5-flash'
    global client
    if not client:
        client = genai.Client(api_key=GEMINI_API_KEY)

    # -------------------------------------------------------------------------
    # HELPER: Safe JSON Generation with Retry/Repair
    # -------------------------------------------------------------------------
    def _generate_chunk(prompt_text, chunk_desc):
        print(f"DEBUG: Generating {chunk_desc}...")
        generation_config = {
            "max_output_tokens": 15000,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "menu": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "day": {"type": "integer"},
                                "day_name": {"type": "string"},
                                "total_kcal": {"type": "integer"},
                                "breakfast": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "kcal": {"type": "integer"},
                                        "ingredients": {"type": "array", "items": {"type": "string"}},
                                        "preparation_steps": {"type": "array", "items": {"type": "string"}},
                                        "time_minutes": {"type": "integer"},
                                        "cost_level": {"type": "string"},
                                        "place": {"type": "string"}
                                    },
                                    "required": ["title", "ingredients", "preparation_steps"]
                                },
                                "lunch": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "kcal": {"type": "integer"},
                                        "ingredients": {"type": "array", "items": {"type": "string"}},
                                        "preparation_steps": {"type": "array", "items": {"type": "string"}},
                                        "time_minutes": {"type": "integer"},
                                        "cost_level": {"type": "string"},
                                        "place": {"type": "string"}
                                    },
                                    "required": ["title", "ingredients", "preparation_steps"]
                                },
                                "dinner": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "kcal": {"type": "integer"},
                                        "ingredients": {"type": "array", "items": {"type": "string"}},
                                        "preparation_steps": {"type": "array", "items": {"type": "string"}},
                                        "time_minutes": {"type": "integer"},
                                        "cost_level": {"type": "string"},
                                        "place": {"type": "string"}
                                    },
                                    "required": ["title", "ingredients", "preparation_steps"]
                                },
                                "snack": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "kcal": {"type": "integer"},
                                        "ingredients": {"type": "array", "items": {"type": "string"}},
                                        "preparation_steps": {"type": "array", "items": {"type": "string"}}
                                    }
                                },
                                "micro_advice": {"type": "string"}
                            },
                            "required": ["day", "breakfast", "lunch", "dinner", "snack"]
                        }
                    },
                    "shopping_list": {
                        "type": "object",
                        "properties": {
                            "protein": {"type": "array", "items": {"type": "string"}},
                            "veg": {"type": "array", "items": {"type": "string"}},
                            "carbs": {"type": "array", "items": {"type": "string"}},
                            "dairy": {"type": "array", "items": {"type": "string"}},
                            "misc": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["protein", "veg", "carbs", "dairy", "misc"]
                    }
                },
                "required": ["menu", "shopping_list"]
            }
        }

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    max_output_tokens=15000,
                    response_mime_type="application/json",
                    response_schema=generation_config["response_schema"],
                    safety_settings=SAFETY_SETTINGS,
                    # timeout is handled at client or elsewhere
                )
            )
            
            # [Added] Granular Logging
            try:
                if response.usage_metadata:
                    i_tok = response.usage_metadata.prompt_token_count
                    o_tok = response.usage_metadata.candidates_token_count
                    
                    from core.ai_usage_logger import log_ai_usage
                    # user_profile is available from outer scope
                    u_id = user_profile.get('telegram_id') 
                    log_ai_usage(None, u_id, f"menu_{chunk_desc}", input_tokens=i_tok, output_tokens=o_tok, model=model_name)
            except Exception as log_e:
                print(f"Usage Log Error: {log_e}")
                
        except Exception as api_error:
            if "429" in str(api_error) or "quota" in str(api_error).lower():
                 raise Exception("AI charchadi (Limit tugadi). Iltimos, 1-2 daqiqadan keyin urinib ko'ring.")
            raise Exception(f"Google API Error: {api_error}")

        response_text = response.text
        if not response_text:
            if hasattr(response, 'prompt_feedback'):
                 feedback = response.prompt_feedback
                 print(f"DEBUG: Safety Feedback: {feedback}")
                 raise Exception(f"Blocked by Safety Filters: {feedback}")
            raise Exception("Empty AI response")

        print(f"DEBUG: AI Output ({model_name}): {response_text[:200]}...")

        # Repair Logic (Compact)
        import re, json
        start_match = re.search(r'\{', response_text)
        clean_json = response_text[start_match.start():] if start_match else response_text
        # Remove any markdown code block suffix if present
        clean_json = clean_json.split('```')[0].strip()
        try:
             return json.loads(clean_json)
        except json.JSONDecodeError as e:
             print(f"Initial JSON Parse Error for {chunk_desc}: {e}. Attempting repair...")
             # Quick Close
             try:
                 repaired = clean_json
                 if repaired.count('"') % 2 != 0: repaired += '"'
                 repaired += '}' * (repaired.count('{') - repaired.count('}'))
                 repaired += ']' * (repaired.count('[') - repaired.count(']'))
                 data = json.loads(repaired)
                 print(f"Repair successful for {chunk_desc} (Method 1: Auto-close).")
                 return data
             except:
                 try:
                    # Trim Last Comma
                    last_comma = clean_json.rfind(',')
                    if last_comma > 0:
                        repaired = clean_json[:last_comma]
                        repaired += '}' * (repaired.count('{') - repaired.count('}')) 
                        repaired += ']' * (repaired.count('[') - repaired.count(']'))
                        data = json.loads(repaired)
                        print(f"Repair successful for {chunk_desc} (Method 2: Trim & Close).")
                        return data
                    else:
                        raise Exception("No comma to backtrack")
                 except Exception as final_e:     
                    raise Exception(f"Failed to repair {chunk_desc} JSON: {final_e}")

    # -------------------------------------------------------------------------
    # MAIN SPLIT LOGIC
    # -------------------------------------------------------------------------
    try:
        base_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
        
        # PART 1: Days 1-3
        prompt_1 = base_prompt + "\n\n🚨 IMPORTANT TASK: Generate ONLY Days 1, 2, and 3. Return an EMPTY shopping_list for now."
        data_1 = _generate_chunk(prompt_1, "Days 1-3")
        
        # PART 2: Days 4-7 + Shopping List
        # We pass summary of Part 1 to help context, but minimal
        # The model is instructed to generate the full shopping list for the whole week in Part 2.
        prompt_2 = base_prompt + f"\n\n✅ Days 1-3 Generated Successfully. Now generate remaining.\n\n🚨 IMPORTANT TASK: Generate ONLY Days 4, 5, 6, and 7. \nAND generate valid 'shopping_list' for THE WHOLE WEEK (Days 1-7)."
        data_2 = _generate_chunk(prompt_2, "Days 4-7")
        
        merged_data = {
            "menu": final_menu,
            "shopping_list": final_shopping
        }
        
        # Basic Validation
        if len(merged_data['menu']) < 2:
            print("WARNING: Merged menu has < 2 days. Might be error.")
            
        # ----------------------------------------------------------------
        # ROBUST CLEANING (Fix "tuzat" and other AI glitches)
        # ----------------------------------------------------------------
        if "menu" in merged_data and isinstance(merged_data["menu"], list):
            for day in merged_data["menu"]:
                 for meal in ["breakfast", "lunch", "dinner", "snack"]:
                     if meal in day and isinstance(day[meal], str):
                         # Remove "tuzat" or similar command leaks
                         clean_text = day[meal].replace(" tuzat", "").replace(" yoz", "")
                         
                         # Ensure capitalization
                         if clean_text:
                             clean_text = clean_text[0].upper() + clean_text[1:]
                             
                         day[meal] = clean_text

        if "shopping_list" in merged_data and isinstance(merged_data["shopping_list"], dict):
            for category in merged_data["shopping_list"]:
                if isinstance(merged_data["shopping_list"][category], list):
                    new_list = []
                    for item in merged_data["shopping_list"][category]:
                        if isinstance(item, str):
                            clean_item = item.replace(" tuzat", "").strip()
                            if clean_item:
                                 new_list.append(clean_item)
                    merged_data["shopping_list"][category] = new_list
        # ----------------------------------------------------------------

        # SAVE TO CACHE
        try:
            # Ensure it's valid data before saving
            if "menu" in merged_data and "shopping_list" in merged_data:
                 db.create_menu_template(
                     profile_key,
                     json.dumps(merged_data["menu"]),
                     json.dumps(merged_data["shopping_list"])
                 )
        except Exception as e:
             print(f"Cache Save Error: {e}")
        return merged_data
            


    except Exception as e:
        print(f"Split Generation Failed: {e}")
        # RE-RAISE THE EXACT ERROR so bot/workout.py displays it
        raise e
        


def ai_answer_question(question):
    """Answers a general fitness question using Gemini."""
    AI_USAGE_STATS["chat"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    response_text = call_gemini(f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}")
    if response_text:
        return format_gemini_text(response_text, "Savolingizga javob")
            
    return "⚠️ AI hozircha band. Iltimos, keyinroq urinib ko‘ring."

def ai_generate_shopping_list(user_profile):
    """Generates a shopping list based on user profile and health context."""
    AI_USAGE_STATS["shopping"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    # Build allergy/health warning
    allergy_text = user_profile.get('allergies')
    health_context = ""
    if allergy_text and allergy_text.lower() not in ['yo\'q', 'no', 'none', 'yoq']:
        health_context = f"\n⚠️ DIQQAT: Foydalanuvchida {allergy_text} ga allergiya bor. Ro'yxatga bularni qo'shmang!\n"
        
    prompt = f"""
    Foydalanuvchi maqsadi: {user_profile.get('goal')}
    {health_context}
    
    Vazifa: 3 kunlik sog'lom ovqatlanish uchun kerakli mahsulotlar ro'yxatini tuzing.
    
    📌 SHARTLAR:
    1. O'zbekiston bozorida oson topiladigan mahsulotlar bo'lsin (Bozor/Korzinka).
    2. Qimmat va kamyob narsalar (kinoa, avokado, losos) o'rniga mahalliy muqobillarini yozing.
    3. Agar allergiya bo'lsa, qat'iy inobatga oling.
    
    FORMAT:
    🛒 **Xaridlar Ro'yxati**
    
    **Sabzavot va Mevalar:**
    - ...
    
    **Oqsillar (Go'sht/Tuxum):**
    - ...
    
    **Don mahsulotlari:**
    - ...
    
    Qisqa va aniq bo'lsin.
    Muhim joylarni **qalin** qilib yoz.
    """
    
    response = call_gemini(prompt)
    if response:
        return format_gemini_text(response, "Xaridlar Ro'yxati")
    return None

def analyze_food_image(image_data):
    """
    Analyzes food image using Gemini Vision.
    Returns structured text in Uzbek.
    """
    AI_USAGE_STATS["vision"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    if not GEMINI_API_KEY:
        return None

    import PIL.Image
    import io

    try:
        image = PIL.Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"DEBUG: Image open error: {e}")
        return None

    models_to_try = ['gemini-2.5-flash']
    
    prompt = """
    You are an AI NUTRITIONIST with access to a vast database of food products.
    The photo shows a meal, drink, or packaged product.

    YOUR GOAL: Provide 99% ACCURATE nutrition data.

    STRICT ANALYSIS PROTOCOL:
    1. 🔍 SCAN TEXT: First, read ANY text on the package (Brand, Name, "0.5L", "100g", "Sugar Free").
    2. 🏭 IDENTIFY PRODUCT: If it's a known brand (Coca-Cola, Snickers, Lays, Nestlé, etc.), verify the exact product variant.
    3. 📏 PRECISE VOLUME/WEIGHT: 
       - If you see "0.5L", use exactly 500ml.
       - If it's a standard can, use 330ml.
       - If it's a standard bottle, use 500ml, 1L, or 1.5L based on visual size.
       - DO NOT GUESS if written on the label. USE THE LABEL DATA.
    4. 📚 OFFICIAL DATA: Use the official nutrition facts for that specific product (e.g. Coca-Cola Classic = 42kcal/100ml).
    5. 🧮 CALCULATION:
       - Example: Coca-Cola 0.5L -> 500ml * 0.42 = 210 kcal. (Show this math mentally and output final result).

    OUTPUT FORMAT (Uzbek):
    🍽 <b>Kaloriya Tahlili</b>

    🥘 <b>Mahsulot:</b> [Aniq Brend va Nomi]
    📏 <b>Hajmi:</b> [Aniq o'lchov, masalan 0.5 L]

    🔥 <b>Jami:</b> [Aniq hisob] kkal

    📊 <b>BJU (100g da emas, butun porsiyada):</b>
    🥩 Oqsil: ... g
    🥑 Yog‘: ... g
    🍞 Uglevod: ... g

    <i>Qadoqdagi ma'lumotlar va standartlarga asoslanib hisoblandi.</i> ✅
    """

    # Ensure config is set (idempotent if already set globally, but good to be sure)
    # genai.configure is global, so if it was called at startup, we are good.
    # But we might need to instantiate specific models.

    for model_name in models_to_try:
        try:
            # Reuse global config, just instantiate model
            vision_model = genai.GenerativeModel(model_name)
            
            response = vision_model.generate_content(
                [prompt, image], 
                safety_settings=SAFETY_SETTINGS,
                request_options={'timeout': 30}
            )
            if response.text:
                # Force convert Markdown bold to HTML bold
                import re
                text = response.text
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
        except Exception as e:
            print(f"DEBUG: Vision failed with {model_name}: {e}")
            
    return None

def analyze_food_text(text):
    """
    Analyzes food text description using Gemini.
    Returns structured text in Uzbek.
    """
    AI_USAGE_STATS["vision"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    global model
    if not GEMINI_API_KEY:
        return None

    try:
        # Use global model if available and it supports text (2.5 flash does)
        if not model:
             model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        Foydalanuvchi yedi: "{text}"
        
        Vazifa:
        - Ovqat tarkibi va porsiyasini tahlil qiling.
        - Umumiy kaloriya va BJU (Oqsil, Yog', Uglevod) ni hisoblang.
        
        Javob formati (O'zbek tilida):
        🍽 <b>Kaloriya Tahlili</b>

        🥘 <b>Ovqat:</b> ...
        📏 <b>Porsiya:</b> ...

        🔥 <b>Jami:</b> ... kkal

        📊 <b>BJU:</b>
        🥩 Oqsil: ... g
        🥑 Yog‘: ... g
        🍞 Uglevod: ... g

        <i>Bu taxminiy hisob, lekin kunlik nazorat uchun yetarli.</i> ✅
        """
        
        try:
            # We must use 'generate_content' with 'generation_config' OR just pass timeout?
            # New SDK allows request_options={'timeout': 15}
            # Or generation_config ... let's try direct call arguments if supported, 
            # but standard is generation_config usually for params.
            # Timeout is likely request_option.
            
            # Since version 0.3.0+, we can use logic. 
            # Assuming standard google.generativeai setup.
            # We'll rely on our own Timer wrapping OR use library support.
            # simplest is to trust 'generation_config' or just catch generic socket timeouts.
            # Let's add request_options which is supported in newer SDKs.
            
            response = model.generate_content(
                prompt,
                safety_settings=SAFETY_SETTINGS,
                request_options={'timeout': 20} # 20 seconds strict timeout
            )
            
            if response.text:
                import re
                text = response.text
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
            return None
        except Exception as e:
            # Catch deadline exceeded or other network errors
            if "deadline" in str(e).lower() or "timeout" in str(e).lower():
                return "⚠️ Kechirasiz, AI javob berishga ulgurmadi. Iltimos, qaytadan urinib ko'ring."
            print(f"Gemini Text Error: {e}")
    except Exception as e:
        print(f"Analyze Text Error: {e}")
        return None

def ai_generate_fridge_recipe(user_profile, available_ingredients):
    """
    Generates 1-2 simple recipes based on available ingredients.
    Output is plain text (not JSON) for speed and flexibility.
    """
    AI_USAGE_STATS["meal"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    prompt = f"""
Siz professional oshpazsiz.
Foydalanuvchi maqsadi: {user_profile.get('goal')}
Bor mahsulotlar: {available_ingredients}

VAZIFA:
Shu mahsulotlardan 1 ta eng zo'r va tez pishadigan retsept yozing.

QAT'IY QOIDALAR:
1. ⚠️ JUDA QISQA BO'LSIN (Maksimal 200 belgi).
2. 🚫 Uydan yo'q narsa qo'shmang (faqat tuz/yog'/suv mumkin).
3. 📝 Format: 
   "🍳 [Nom]"
   "🥣 [Masalliqlar]"
   "👨‍🍳 [1 gap bilan tayyorlash]"
   
NAMUNA:
🍳 Pomidorli Tuxum
🥣 2 tuxum, 1 pomidor, tuz
👨‍🍳 Pomidorni to'g'rab qovuring, ustiga tuxumni chaqib, tuz sepib 5 daqiqa pishiring. Yoqimli ishtaha!
"""
    return call_gemini(prompt)

def format_gemini_text(raw_text, title):
    """Cleans and formats AI output."""
    if not raw_text:
        return ""
    
    import html
    import re
    
    # 1. Escape HTML special characters first (safe from random < or >)
    # quote=False ensures ' and " are not escaped, preventing &x27; issues
    text = html.escape(raw_text, quote=False)
    
    # 2. Convert Markdown bold (**text**) to HTML (<b>text</b>)
    # This regex finds **text** and replaces it with <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 3. Clean up any remaining Markdown artifacts if needed
    text = text.replace("##", "").replace("#", "")
    
    return f"<b>{title}</b>\n\n{text}"

def ai_provide_psychological_support(reason):
    """Provides psychological support based on user's mood reason."""
    AI_USAGE_STATS["support"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    prompt = f"""
    Foydalanuvchi kayfiyati yomonligini aytdi. Sababi: "{reason}"
    
    Vazifa:
    - Unga qisqa, dalda beruvchi va psixologik yordam beruvchi xabar yoz.
    - Agar muammo jiddiy bo'lsa, oddiy maslahat ber (nafas olish mashqi, sayr qilish, va h.k.).
    - Do'stona va samimiy ohangda bo'lsin.
    - Maksimal 500 belgi.
    - O'zbek tilida.
    
    Javob formati:
    [Matn]
    """
    
    response_text = call_gemini(prompt)
    if response_text:
        return response_text
    return "Tushunaman, ba'zida shunday kunlar bo'ladi. O'zingizni ehtiyot qiling va chuqur nafas oling. 💚"

def ai_generate_weekly_workout_json(user_profile):
    """
    Generates a 7-DAY Weekly Workout Plan in strict JSON format.
    Mirrors the logic of the menu system.
    """
    AI_USAGE_STATS["workout"] += 1
    AI_USAGE_STATS["total_requests"] += 1
    
    # 0. CACHE CHECK
    from core.db import db
    import json
    
    # Workout depends on same factors
    profile_key = get_profile_key(user_profile)
    cached = db.get_workout_template(profile_key)
    
    if cached:
        print(f"DEBUG: Cache Hit for Workout: {profile_key}")
        try:
             # Just return what we need. The caller likely expects the Raw JSON string or Dict?
             # ai_generate_weekly_workout_json usually returns Dict.
             return json.loads(cached['workout_json'])
        except Exception as e:
             print(f"Cache Corrupt: {e}")
    
    goal = user_profile.get('goal', 'Sog‘liq')
    
    # 1. System Prompt (JSON enforcer)
    from core.exercises import get_exercises_string
    
    # 1. System Prompt (JSON enforcer)
    # 1. System Prompt (JSON enforcer)
    # 1. System Prompt (JSON enforcer)
    system_prompt = f"""
ROLE:
You are a professional fitness coach system for a Telegram bot.
Your task is to generate REALISTIC, SAFE, EFFECTIVE workout plans using ONLY the exercises provided below.

{get_exercises_string()}

IMPORTANT RULES:
1. USE ONLY EXERCISES FROM THE LIST ABOVE. DO NOT INVENT EXERCISES.
2. If the user goal is weight loss, focus on high reps and cardio-style intervals.
3. If the user goal is muscle gain, focus on hypertrophy ranges (8-12 reps).

❌ You MUST NOT invent new exercises
❌ You MUST NOT change exercise names
❌ You MUST NOT remove Instagram links
❌ You MUST NOT generate workouts every single day

⸻

🧠 CORE RULES (VERY IMPORTANT)
	1.	ONLY use the exercise list provided below
	2.	Workout plans must include:
	•	Rest days
	•	Warm-up section
	•	Clear sets, reps, rest
	3.	No consecutive training of the same muscle group
	4.	Beginner-friendly, realistic recovery
	5.	Output must be CLEAR, HUMAN-READABLE, Telegram-ready

⸻

🗓 WORKOUT STRUCTURE RULES

Weekly logic:
	•	3–4 workout days per week
	•	1–2 rest days
	•	Muscle split logic:
	•	Upper Body -> Yuqori Tana
	•	Lower Body -> Pastki Tana
	•	Core / Full Body -> Butun Tana
	•	Never train same muscle groups on consecutive days

⸻

📦 EXERCISE DATABASE (ONLY SOURCE)

{get_exercises_string()}

⸻

🏋️ DAY OUTPUT FORMAT (The 'exercises' field in JSON)

For workout days, the 'exercises' string MUST look exactly like this (use HTML bold tags <b>):

🏋️ Bugungi mashq rejasi ({{Yuqori Tana / Pastki Tana / Butun Tana}})

⏱ Umumiy vaqt: 30–40 daqiqa
🎯 Maqsad: {{Vazn yo'qotish / Mushak o'stirish}} (Uzbek)

🔹 <b>Razminka (5 daqiqa)</b>
- Yengil cho‘zilish
- Bo‘g‘imlarni aylantirish
- Yengil harakatlar

💪 <b>Asosiy mashqlar</b>

1️⃣ <b>Exercise Name</b>
📌 Mushaklar: (Uzbek)
🔁 3 set × 12 marta
⏸ Dam: 60 soniya
🎥 Link: <a href="Instagram URL">Video darslik</a>

2️⃣ <b>Next Exercise Name</b>
... (Repeat for 4-5 exercises) ...

🧘 <b>Sovitish</b>
- Mushaklarni cho'zish

❌ DO NOT ADD SEPARATOR LINES LIKE "_______________________" AT THE END.

---

For REST DAYS, the 'exercises' field MUST be exactly:
"🧘‍♂️ <b>Bugun dam olish kuni</b>\\n\\nBugun tanani tiklaymiz.\\nYengil yurish yoki cho‘zilish tavsiya etiladi.\\n\\n👉 Ertaga mashq rejalashtirilgan"

⸻

OUTPUT FORMAT: JSON ONLY

{{
  "schedule": [
    {{
      "day": 1,
      "focus": "Yuqori Tana",
      "exercises": "...formatted string as above..."
    }},
    ... (for 7 days)
  ]
}}
"""

    # 2. User Prompt (Context)
    user_prompt = f"""
Foydalanuvchi ma'lumotlari:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {goal}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik: {user_profile.get('activity_level', 'O’rtacha')}

Talablar:
- 7 kunlik reja (JSON array "schedule" ichida). 
- DIQQAT: "schedule" array ichida roppa-rosa 7 ta element bo'lishi SHART.
- Dam olish kunlarini ham kiriting (masalan, 4-kun: Dam olish va tiklanish).
- JSON valid bo'lsin.
"""

    # ... (Prompt setup)

    # 3. Call AI
    import json
    try:
        response_text = ask_gemini(system_prompt, user_prompt)
        # Clean markdown
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response_text)
        
        # Validate structure
        if "schedule" not in data or not isinstance(data["schedule"], list):
            raise Exception("Invalid JSON structure: missing 'schedule' list")
            
        if len(data["schedule"]) < 7:
             print("DEBUG: AI generated less than 7 days. Accepting partial but logging warning.")

        # VALIDATE CONTENT
        import re
        for day in data["schedule"]:
            if "exercises" not in day or not day.get("exercises"):
                day["exercises"] = "<i>Dam olish yoki yengil mashqlar</i>"
            else:
                # 1. Force spacing between numbered items (e.g. "1. Exercise" -> "\n\n1. Exercise")
                # Look for digit+dot at start of line OR preceded by newline/space
                clean_ex = day["exercises"]
                if "1." in clean_ex and "2." in clean_ex:
                     # Regex: find (digit dot) and ensure it has \n\n before it (unless it's the very start)
                     # Using a simple approach: Replace all "<br>" with "\n", then "\n" with "\n\n"
                     # But safer to just target the numbers.
                     
                     # First, clean existing newlines
                     clean_ex = clean_ex.replace("<br>", "\n").replace("\\n", "\n")
                     
                     # Replace any sequence of newlines before a number with exactly \n\n
                     clean_ex = re.sub(r'\s*(\d+\.)', r'\n\n\1', clean_ex)
                     
                     # Remove leading \n\n if added to the first item
                     clean_ex = clean_ex.lstrip()
                     
                     day["exercises"] = clean_ex
            
            # Fix 'focus' having weird suffixes if any
            if "focus" in day:
                day["focus"] = day["focus"].replace(" tuzat", "").replace(" mashqlari", "")
             
        # SAVE TO CACHE
        try:
             # data["schedule"] is the list we want to cache, or the whole data?
             # get_workout_template returns loaded json of cached['workout_json']
             # create_workout_template takes json string.
             # In cache check, we return json.loads(cached['workout_json']).
             # So we should save json.dumps(data["schedule"]).
             # Verify data["schedule"] is what we want. Yes.
             db.create_workout_template(profile_key, json.dumps(data["schedule"]))
        except Exception as e:
             # handle unique constraint or race conditions
             print(f"Workout Cache Save Warning: {e}")

        return data

    except Exception as e:
        print(f"Error generating weekly workout JSON: {e}")
        return None

# -------------------------------------------------------------------------
# NEW: Single Meal Generation (VIP Swap)
# -------------------------------------------------------------------------
def ai_generate_single_meal(user_profile, meal_type, day_name="Bugun"):
    """Generates a SINGLE meal object for VIP swap."""
    
    # 1. Prompt
    prompt = f"""
    Siz professional dietologsiz.
    Vazifa: "{day_name}" uchun yangi "{meal_type.upper()}" (Taom) o'ylab toping.
    
    Foydalanuvchi:
    - Maqsad: {user_profile.get('goal', 'Sog‘liq')}
    - Allergiya: {user_profile.get('allergies', 'Yo‘q')}
    
    TALABLAR:
    - 1 ta ovqat varianti.
    - JSON formatda.
    - Kaloriya: 300-600 kkal oralig'ida bo'lsin.
    
    JSON SCHEMA:
    {{
        "title": "Taom nomi",
        "kcal": 450,
        "ingredients": ["..."],
        "preparation_steps": ["..."],
        "time_minutes": 15,
        "cost_level": "O'rtacha",
        "place": "uy"
    }}
    """
    
    try:
         # Use the new structured generation if possible, strictly enforcing schema
         response = curr_model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "kcal": {"type": "integer"},
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "preparation_steps": {"type": "array", "items": {"type": "string"}},
                        "time_minutes": {"type": "integer"},
                        "cost_level": {"type": "string"},
                        "place": {"type": "string"}
                    },
                    "required": ["title", "kcal", "ingredients", "preparation_steps"]
                }
            },
            request_options={'timeout': 25}
         )
         
         # Log usage
         if response.usage_metadata:
             try:
                 from core.ai_usage_logger import log_ai_usage
                 log_ai_usage(None, user_profile.get('telegram_id'), "meal_swap_vip", 
                              input_tokens=response.usage_metadata.prompt_token_count,
                              output_tokens=response.usage_metadata.candidates_token_count)
             except: pass

         import json
         return json.loads(response.text)
         
    except Exception as e:
        print(f"Single Meal Gen Error: {e}")
        return None

# -------------------------------------------------------------------------
# NEW: Free Tier Static Templates (Zero AI)
# -------------------------------------------------------------------------

def get_free_workout_template(user_profile):
    """Returns a STATIC workout plan based on goal. No AI cost."""
    goal = user_profile.get('goal', 'Sog‘liq')
    is_weight_loss = "Ozish" in goal or "weight_loss" in goal or "Vazn tashlash" in goal
    
    # Template 1: Weight Loss (Uy sharoiti)
    if is_weight_loss:
        return {
            "schedule": [
                {
                    "day": 1,
                    "focus": "Pastki tana",
                    "exercises": "1. Squat — 3×12\n2. O‘tirib turish (Chair squat) — 3×15\n3. Oyoq ko‘tarish (Leg raise) — 3×10\n4. Yengil cho‘zilish — 5 daqiqa"
                },
                {
                    "day": 2,
                    "focus": "Dam olish (Rest)", 
                    "exercises": "Bugun to'liq tiklanish kuni. Ko'proq suv iching."
                },
                {
                    "day": 3,
                    "focus": "Yuqori tana",
                    "exercises": "1. Knee push-up — 3×10\n2. Devorga suyangan push-up — 3×12\n3. Yelka aylantirish — 3×15\n4. Cho‘zilish — 5 daqiqa"
                },
                {
                    "day": 4,
                    "focus": "Dam olish (Rest)",
                    "exercises": "Sayr qiling va dam oling."
                },
                {
                    "day": 5,
                    "focus": "Core + Kardio",
                    "exercises": "1. Plank — 3×20 soniya\n2. Crunch — 3×12\n3. Joyida yurish — 5 daqiqa\n4. Nafas mashqlari — 3 daqiqa"
                },
                {
                    "day": 6,
                    "focus": "Dam olish (Rest)",
                    "exercises": "Haftalik yakun."
                },
                {
                    "day": 7,
                    "focus": "Dam olish (Rest)",
                    "exercises": "Yangi haftaga tayyorgarlik."
                }
            ]
        }
    
    # Template 2: Muscle Gain / General (Zal/Uy)
    return {
        "schedule": [
            {
                "day": 1,
                "focus": "Ko‘krak + Qo‘l",
                "exercises": "1. Push-up — 4×10\n2. Dumbbell curl — 3×12\n3. Triceps dip — 3×10"
            },
            {
                "day": 2,
                "focus": "Dam olish (Rest)",
                "exercises": "Mushaklar o'sishi uchun dam kerak."
            },
            {
                "day": 3,
                "focus": "Oyoq",
                "exercises": "1. Squat — 4×12\n2. Lunge — 3×10\n3. Calf raise — 3×15"
            },
            {
                "day": 4,
                "focus": "Dam olish (Rest)",
                "exercises": "Tiklanish kuni."
            },
            {
                "day": 5,
                "focus": "Yelka + Core",
                "exercises": "1. Shoulder press — 3×10\n2. Plank — 3×30 soniya"
            },
            {
                "day": 6,
                "focus": "Dam olish (Rest)",
                "exercises": "Dam olish."
            },
            {
                "day": 7,
                "focus": "Dam olish (Rest)",
                "exercises": "Tayyorgarlik."
            }
        ]
    }

def get_free_menu_template():
    """Returns a STATIC 1-day menu template. Zero AI cost."""
    # This is a 1-day template replicated for structure compliance
    # But for Free users, we only show "Bugungi Menyu".
    
    daily_plan = {
        "day": 1,
        "day_name": "Bugun",
        "total_kcal": 1400,
        "micro_advice": "Siz yaxshi ketayapsiz 🔥. Natija davomiylikda.",
        "breakfast": {
            "title": "Tuxum va sabzavot",
            "kcal": 350,
            "ingredients": ["Tuxum (2 dona)", "Pomidor (1 dona)", "Bodring (1 dona)"],
            "preparation_steps": ["Tuxumni qaynating", "Sabzavotlarni to'g'rang"],
            "time_minutes": 10,
            "cost_level": "Arzon",
            "place": "uy"
        },
        "snack": {
            "title": "Olma",
            "kcal": 150,
            "ingredients": ["Olma (1 dona)"], 
            "preparation_steps": ["Yuvib iste'mol qiling"]
        },
        "lunch": {
            "title": "Tovuq sho‘rvasi",
            "kcal": 500,
            "ingredients": ["Tovuq (150g)", "Kartoshka (1)", "Sabzi (1)"],
            "preparation_steps": ["Go'shtni qaynatib oling", "Sabzavot soling"],
            "time_minutes": 45,
            "cost_level": "Arzon",
            "place": "uy"
        },
        "dinner": {
            "title": "Grechka + salat",
            "kcal": 400,
            "ingredients": ["Grechka (80g)", "Karam (100g)"],
            "preparation_steps": ["Grechkani dimlang", "Salat to'g'rang"],
            "time_minutes": 25,
            "cost_level": "Arzon",
            "place": "uy"
        }
    }
    
    # Replicate for 7 days structure (so JSON parsing doesn't break)
    menu_list = []
    
    # Locked Meal Object
    locked_meal = {
         "title": "🔒 Faqat Premiumda",
         "kcal": 0,
         "ingredients": ["..."],
         "preparation_steps": ["YASHA Plus taomnomasi"],
         "time_minutes": 0,
         "cost_level": "-",
         "place": "-"
    }

    for i in range(1, 8):
        if i == 1:
            menu_list.append(daily_plan)
        else:
            day_copy = {
                "day": i,
                "day_name": f"Kun {i} (Premium)",
                "total_kcal": 0,
                "micro_advice": "To'liq menyu faqat YASHA Plus'da.",
                "breakfast": locked_meal,
                "lunch": locked_meal,
                "dinner": locked_meal,
                "snack": locked_meal
            }
            menu_list.append(day_copy)
        
    return {
        "menu": menu_list,
        "shopping_list": {} # Empty for Free
    }

# -------------------------------------------------------------------------
# NEW: Fridge / Recipe Suggestion (Premium)
# -------------------------------------------------------------------------
def ai_suggest_recipe(user_profile, ingredients_text):
    """Suggests a healthy recipe based on user ingredients."""
    
    prompt = f"""
    Siz professional dietologsiz.
    
    Foydalanuvchi maqsadi: {user_profile.get('goal', 'Sog‘liq')}
    Muzlatgichda bor mahsulotlar: "{ingredients_text}"
    
    VAZIFA:
    Shu mahsulotlardan (va qo'shimcha oddiy narsalardan) foydalanib, 
    bitta sog'lom va foydali retsept tuzing.
    
    Javob formati (O'zbek tilida):
    🍽 **Taom nomi**
    
    🛒 **Kerakli masalliqlar:**
    - ...
    
    👩‍🍳 **Tayyorlash:**
    1. ...
    2. ...
    
    💡 **Foydasi:** ...
    
    Qisqa, lo'nda va tushunarli bo'lsin.
    """
    
    try:
        response = curr_model.generate_content(
            prompt,
            request_options={'timeout': 30}
        )
        
        # Log usage
        if response.usage_metadata:
             try:
                 from core.ai_usage_logger import log_ai_usage
                 log_ai_usage(None, user_profile.get('telegram_id'), "fridge_recipe", 
                              input_tokens=response.usage_metadata.prompt_token_count,
                              output_tokens=response.usage_metadata.candidates_token_count)
             except: pass
             
        return response.text
             
    except Exception as e:
        print(f"Fridge Gen Error: {e}")
        return None

# -------------------------------------------------------------------------
# Free Tier Mood Support (Static)
# -------------------------------------------------------------------------
def get_free_mood_support_template():
    """Returns a static supportive message for Free users."""
    import random
    
    templates = [
        (
            "😔 **Tushunaman, ba'zan shunday bo'ladi.**\n\n"
            "Hozir eng muhimi — o'zingizga vaqt ajratish. "
            "Chuqur nafas oling va bir stakan suv iching. "
            "Muammolar vaqtinchalik, siz esa kuchlisiz. ��\n\n"
            "💡 _YASHA Plus'da AI sizning vaziyatingizni tahlil qilib, "
            "aniq psixologik maslahatlar bera oladi._"
        ),
        (
            "🫂 **Siz yolg'iz emassiz.**\n\n"
            "Har bir inson qiyin kunlarni boshdan kechiradi. "
            "Bugun shunchaki dam olishga harakat qiling. "
            "Hammasi yaxshi bo'ladi ✨\n\n"
            "💡 _YASHA Plus'da AI murabbiy siz bilan suhbatlashib, "
            "stressni yengishga yordam beradi._"
        ),
        (
            "🌧 **Yomg'irdan keyin albatta quyosh chiqadi.**\n\n"
            "Kayfiyat o'zgaruvchan, lekin maqsadingiz o'zgarmasin. "
            "O'zingizni ehtiyot qiling.\n\n"
            "�� _YASHA Plus foydalanuvchilari uchun AI har qanday vaziyatda "
            "individual yechim taklif qiladi._"
        )
    ]
    return random.choice(templates)
