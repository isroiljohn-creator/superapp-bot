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
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error initializing Gemini: {e}")

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

def call_gemini(prompt):
    """Sends prompt to Gemini and returns text."""
    if not model:
        return None
    
    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
    return None

def format_ai_text(raw_text, title):
    """Cleans and formats AI output."""
    if not raw_text:
        return ""
    
    # Clean up Markdown
    text = raw_text.replace("**", "").replace("##", "").replace("#", "")
    
    # Ensure no dangerous HTML
    text = text.replace("<script>", "").replace("</script>", "")
    
    # Limit length (soft limit)
    if len(text) > 1500:
        text = text[:1500] + "..."
        
    # Add Title
    formatted = f"🍽 <b>{title}</b>\n\n{text.strip()}"
    return formatted

def ai_generate_workout(user_profile):
    """Generates a weekly workout plan using Gemini or fallback."""
    prompt = f"""
Siz Telegram uchun qisqa, silliq, tushunarli mashq rejalari tuzadigan professional fitness trenerisiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Maqsad: {user_profile.get('goal')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}

🎯 Vazifa:
Foydalanuvchiga uy sharoitida bajariladigan 4 kunlik mashq rejasi tuzing.

📌 FORMAT TALABLARI:
- HTML ishlatma (<p>, <ul>, <li> yo‘q).
- Faqat oddiy matn + <b>qalin</b> joylar.
- Emojilarni minimal ishlat (faqat bo‘lim sarlavhalarida).
- Har bir kun quyidagicha struktura bo‘lsin:

<b>1-kun: Ko‘krak & Triceps</b>  
• Mashq 1 — takrorlar  
• Mashq 2 — takrorlar  
• Mashq 3 — takrorlar  

<b>2-kun: Oyoq & Yelka</b>  
• ...

<b>3-kun: Dam olish</b>  
• Qisqa maslahat yozing (1–2 jumla)

<b>4-kun: Orqa & Core</b>  
• ... 

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.
🧩 Har bir mashq sodda va uyda qilinadigan bo‘lsin.
🧩 Javob faqat matn ko‘rinishida bo‘lsin, HTML teglarsiz.
"""
    
    response_text = call_gemini(prompt)
    if response_text:
        return format_ai_text(response_text, "Sizning mashg‘ulot rejangiz")
        
    return get_offline_workout(user_profile)

def ai_generate_menu(user_profile):
    """Generates a weekly meal plan using Gemini or fallback."""
    prompt = f"""
Siz Telegram uchun ovqatlanish bo‘yicha qisqa, silliq, o‘qilishi oson matn yozadigan dietologsiz.

Foydalanuvchi profili:
Yosh: {user_profile.get('age')}
Jins: {user_profile.get('gender')}
Bo‘y: {user_profile.get('height')}
Vazn: {user_profile.get('weight')}
Maqsad: {user_profile.get('goal')}
Allergiya: {user_profile.get('allergy')}

🎯 Vazifa:
Foydalanuvchiga 7 kunlik ovqatlanish rejasi tuzing. Juda uzun bo‘lmasin — odam Telegramda o‘rtacha 700–900 belgi o‘qiydi.

📌 MUHIM FORMAT TALABLARI:
- Hech qanday HTML (<p>, <br>, <ul>, <li>) ishlatma.
- Faqat matn + <b>qalin</b> joylar.
- Emojilarni kam ishlat — faqat kun nomlarida yoki sarlavhalarda.
- Har kun quyidagicha bo‘lsin:

<b>1-kun</b>
• Nonushta: ...
• Tushlik: ...
• Kechki: ...
• Snack: ...

- 7 kunda ham struktura bir xil bo‘lsin.
- Oxirida alohida blokda:

<b>Xarid ro‘yxati</b>
• ...

🧩 Matn juda uzun chiqmasin. Maksimal 1500 belgi.

📢 Javob faqat matn ko‘rinishida bo‘lsin, HTML teglarsiz!
"""

    response_text = call_gemini(prompt)
    if response_text:
        return format_ai_text(response_text, "Sizning ovqatlanish rejangiz")

    return get_offline_menu(user_profile)

def ai_answer_question(question):
    """Answers a general fitness question using Gemini."""
    response_text = call_gemini(f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}")
    if response_text:
        return format_ai_text(response_text, "Savolingizga javob")
            
    return "⚠️ AI hozircha band. Iltimos, keyinroq urinib ko‘ring."
