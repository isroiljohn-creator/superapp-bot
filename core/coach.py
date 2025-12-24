import random
from datetime import datetime
from core.db import db
from core.flags import is_flag_enabled

# 20 Approved Coach Templates (Uzbek, "SIZ" respectful tone)
COACH_TEMPLATES = {
    "motivation": [
        "Bugun juda katta narsa shart emas — SIZdan kichik qadam kerak. 10 daqiqa harakat ham ritmni saqlab qoladi. 💪",
        "SIZ to‘xtab qolmadingiz — bu eng muhim yutuq. Bugun bir narsani tanlang: suv yoki yengil mashq.",
        "Kayfiyat bo‘lmasa ham harakat ishlaydi. SIZ bugun o‘zingizga isbot qilasiz: “men davom etaman”.",
        "Tanangiz natijani sekin beradi, lekin har kuni “ha” desangiz albatta beradi. Bugun ham o‘zingizga sodiq qoling.",
        "Bugun o‘zingizni yengmang — o‘zingizga yordam bering. Yengil, lekin izchil qadam.",
        "SIZning kuchingiz motivatsiyada emas, odatda. Bugun bitta odatni yopamiz. ✅",
        "Har kuni ideal bo‘lish shart emas. Muhimi: SIZ tizimni tashlab ketmaysiz. 🔥"
    ],
    "discipline": [
        "Bugun reja oddiy: suv + ovqatni nazorat. SIZ nazorat qilsangiz, natija keladi.",
        "Bugun “kayfiyat” emas, “jadval” ishlaydi. 15 daqiqa harakat — va tamom.",
        "SIZga ilhom kerak emas. SIZga ketma-ketlik kerak. Bugun ketma-ketlikni saqlaymiz.",
        "Bugun oson variant tanlang, lekin tashlab ketmang. Eng yomon mashq — qilinmagan mashq.",
        "Agar bugun vaqt kam bo‘lsa, qisqartiring — bekor qilmang. 5–10 daqiqa ham hisob.",
        "Bugun “keyin” demaymiz. Hozir bitta kichik ish: suv iching yoki yurib keling. 🚶"
    ],
    "recovery": [
        "Dam olish ham rejaning bir qismi. SIZ bugun tanaga tiklanish berib, ertaga kuchliroq bo‘lasiz.",
        "Agar charchoq bo‘lsa, yengil yurish yetarli. Bugun tanani “sindirmaymiz”, “qo‘llab-quvvatlaymiz”.",
        "Bugun uyquni ustun qiling. SIZ uyquni to‘g‘rilasangiz, ishtaha ham, energiya ham joyiga tushadi. 😴",
        "Bugun tanangizga rahmat ayting: u siz uchun ishlayapti. Yengil harakat + ko‘proq suv."
    ],
    "consistency": [
        "SIZning natijangiz “bir kun” emas, “ketma-ket kunlar”dan chiqadi. Bugun yana bitta kunni yutamiz. ✅",
        "Bugun faqat bitta narsani bajaring — lekin bajaring. Bu SIZning yangi standartingiz bo‘ladi.",
        "Agar kecha chiqmagan bo‘lsa ham muammo emas. Bugun qaytamiz. SIZ qaytganingiz — kuch. 💚"
    ]
}

def get_coach_message(user_id, force_refresh=False):
    """
    Get or generate today's coach message.
    """
    if not is_flag_enabled("coach_zone", user_id, default=True):
        return None
        
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    # 1. Check existing
    if not force_refresh:
        existing = db.get_today_coach_message(user_id, date_str)
        if existing:
            return existing
            
    # 2. Generate New
    user = db.get_user(user_id)
    if not user: return None
    
    # Decision: Premium vs Free
    is_premium = db.is_premium(user_id)
    
    msg_text = ""
    
    if is_premium:
        # TODO: Connect Gemini 1.5 Flash here later for personalized message
        # For now, fallback to smart template selection based on day of week
        # Mon=Motivation, Tue=Discipline, Wed=Consistency, Thu=Discipline, Fri=Motivation, Sat/Sun=Recovery
        weekday = datetime.utcnow().weekday()
        if weekday in [5, 6]: category = "recovery"
        elif weekday in [0, 4]: category = "motivation"
        elif weekday == 2: category = "consistency"
        else: category = "discipline"
        
        # Add slight personalization prefix if name exists
        name = user.get('full_name', '').split(' ')[0]
        base_msg = random.choice(COACH_TEMPLATES[category])
        if name and len(name) < 15:
            msg_text = f"{name}, {base_msg.lower().replace('siz', 'Siz', 1)}" # Adjust capitalization roughly
        else:
            msg_text = base_msg
            
    else:
        # FREE: Random template from mixed bag
        all_msgs = []
        for cat in COACH_TEMPLATES:
            all_msgs.extend(COACH_TEMPLATES[cat])
        msg_text = random.choice(all_msgs)
        
    # 3. Save
    db.add_coach_message(user_id, msg_text, date_str)
    
    # 4. Log Analytics
    db.log_event(user_id, "coach_message_generated", {"is_premium": is_premium})
    
    return msg_text
