import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Using 2.5 Flash as requested by user
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("DEBUG: Gemini AI initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
else:
    print("DEBUG: GEMINI_API_KEY not found in environment variables.")

def get_offline_workout(user_profile):
    goal = user_profile.get('goal', 'Sog‘liq')
    name = user_profile.get('name', 'Foydalanuvchi')
    
    header = f"⚠️ <b>AI hozircha band, {name}!</b>\nAmmo sizning maqsadingiz ({goal}) uchun maxsus offline rejani tayyorlab berdim:"
    
    if "Ozish" in goal:
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
    elif "Massa" in goal:
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
    
    if "Ozish" in goal:
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
    elif "Massa" in goal:
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
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Models to try in order
MODELS_TO_TRY = [
    'gemini-2.5-flash'
]

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
    global model
    
    if not GEMINI_API_KEY:
        raise Exception("API Key not found")

    # Combine system and user prompt
    full_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
    
    last_error = None
    
    for model_name in MODELS_TO_TRY:
        try:
            # Configure and instantiate specific model
            genai.configure(api_key=GEMINI_API_KEY)
            current_model = genai.GenerativeModel(model_name)
            
            print(f"DEBUG: Attempting AI generation with model: {model_name}")
            
            response = current_model.generate_content(
                full_prompt, 
                safety_settings=SAFETY_SETTINGS,
                request_options={'timeout': 60}
            )
            
            if response.text:
                return response.text.strip()
            
        except Exception as e:
            print(f"DEBUG: Model {model_name} failed: {e}")
            try:
                if hasattr(response, 'prompt_feedback'):
                    print(f"DEBUG: Prompt Feedback: {response.prompt_feedback}")
            except:
                pass
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
Foydalanuvchiga uy sharoitida bajariladigan 3 kunlik mashq rejasi tuzing.

📌 FORMAT TALABLARI:
- HTML ishlatma (<p>, <ul>, <li> yo‘q).
- Muhim joylarni ajratish uchun **yulduzcha** (markdown) ishlat.
- Emojilarni minimal ishlat (faqat bo‘lim sarlavhalarida).
- Har bir kun quyidagicha struktura bo‘lsin:

**1-kun: Ko‘krak & Triceps**  
- Mashq 1 — takrorlar  
- Mashq 2 — takrorlar  
- Mashq 3 — takrorlar  

**2-kun: Oyoq & Yelka**  
- ...

**3-kun: Orqa & Core**  
- ... 

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.
🧩 Har bir mashq sodda va uyda qilinadigan bo‘lsin.
🧩 Javob faqat matn ko‘rinishida bo‘lsin.
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
        allergy_section = f"\n\n⚠️ ⚠️ ⚠️ JUDA MUHIM ⚠️ ⚠️ ⚠️\nFoydalanuvchida {allergy_text} ga ALLERGIYA BOR!\nTavsiya qilingan ovqatlarda BU MAHSULOTLAR BO'LMASLIGI KERAK!\nAlternativ mahsulotlar tavsiya qiling.\n"
    
    prompt = f"""
Siz Telegram uchun ovqatlanish bo'yicha qisqa, silliq, o'qilishi oson matn yozadigan dietologsiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Bo'y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Faollik darajasi: {user_profile.get('activity_level', 'Belgilanmagan')}
Maqsad: {user_profile.get('goal')}{allergy_section}

🎯 Vazifa:
Foydalanuvchiga 3 kunlik ovqatlanish rejasi tuzing.

📌 MUHIM SHARTLAR:
1. O'zbekiston bozoriga mos mahsulotlar bo'lsin (avokado, qimmat baliqlar o'rniga — tuxum, tovuq, mol go'shti, mahalliy mevalar).
2. Xaridlar ro'yxatini YOZMANG (bu alohida so'raladi).
3. Agar foydalanuvchida allergiya yoki kasallik bo'lsa, menyuni shunga qarab qat'iy moslang!

📌 FORMAT TALABLARI:
- Hech qanday HTML (<p>, <br>, <ul>, <li>) ishlatma.
- Muhim joylarni ajratish uchun **yulduzcha** (markdown) ishlat.
- Emojilarni kam ishlat — faqat kun nomlarida yoki sarlavhalarda.
- Har kun quyidagicha bo'lsin:

**1-kun**
- Nonushta: ...
- Tushlik: ...
- Kechki: ...
- Snack: ...

- 3 kunda ham struktura bir xil bo'lsin.

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.

📢 Javob faqat matn ko'rinishida bo'lsin.
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

    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash']
    
    prompt = """
    The photo shows a meal.
    You must estimate:
    - dish name / main components
    - approximate portion size
    - total kcal
    - protein / fat / carbs
    
    Respond in short Uzbek text, max ~800 characters, formatted like:
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

    # Ensure config is set (idempotent if already set globally, but good to be sure)
    # genai.configure is global, so if it was called at startup, we are good.
    # But we might need to instantiate specific models.

    for model_name in models_to_try:
        try:
            # Reuse global config, just instantiate model
            vision_model = genai.GenerativeModel(model_name)
            
            response = vision_model.generate_content([prompt, image], safety_settings=SAFETY_SETTINGS)
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
        
        response = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        if response.text:
            import re
            text = response.text
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            return text
        return None
    except Exception as e:
        print(f"Gemini Text Error: {e}")
        return None

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
