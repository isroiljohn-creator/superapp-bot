# Localization dictionary
TRANS = {
    "uz": {
        "select_language": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык / 🇬🇧 Select language",
        "language_selected": "✅ O'zbek tili tanlandi.",
        "welcome": "Assalomu alaykum, {name}! YASHA Fitness Botiga xush kelibsiz.",
        "enter_name": "Ismingizni kiriting:",
        "enter_age": "Yoshingizni kiriting (faqat raqam):",
        "enter_gender": "Jinsingizni tanlang:",
        "male": "Erkak 👨",
        "female": "Ayol 👩",
        "enter_height": "Bo'yingizni kiriting (sm):",
        "enter_weight": "Vazningizni kiriting (kg):",
        "enter_goal": "Maqsadingizni tanlang:",
        "goal_weight_loss": "Ozish 📉",
        "goal_mass_gain": "Massa olish 💪",
        "goal_health": "Sog'lom bo'lish ❤️",
        "allergy_question": "Sizda biron mahsulotga allergiya bormi?",
        "yes": "Ha",
        "no": "Yo'q",
        "enter_allergy": "Qaysi mahsulotlarga allergiyangiz bor? Yozib yuboring:",
        "calculating": "⏳ Ma'lumotlaringiz tahlil qilinmoqda...",
        "onboarding_complete": "✅ Tabriklaymiz! Siz ro'yxatdan o'tdingiz.",
        
        # Main Menu
        "menu_plan": "📅 Mening rejam",
        "menu_profile": "👤 Profil",
        "menu_premium": "💎 Premium",
        "menu_progress": "📈 Natijalarim",
        "menu_feedback": "✍️ Fikr bildirish",
        "menu_settings": "⚙️ Sozlamalar",
        
        # Profile
        "profile_title": "👤 **Sizning Profilingiz**",
        "name": "Ism",
        "age": "Yosh",
        "gender": "Jins",
        "height": "Bo'y",
        "weight": "Vazn",
        "goal": "Maqsad",
        "allergies": "Allergiya",
        "status": "Status",
        "premium": "Premium",
        "free": "Bepul",
        "edit_profile": "✏️ Tahrirlash",
        "back": "Ortga",
        
        # Premium
        "premium_title": "💎 **Premium Obuna**",
        "premium_desc": "Premium obuna bilan siz quyidagilarga ega bo'lasiz:\n\n✅ Individual AI mashq rejasi\n✅ Individual AI ovqatlanish rejasi\n✅ Cheklovsiz so'rovlar\n✅ Tezkor yordam",
        "buy_1_month": "1 oy - 50,000 so'm",
        "buy_3_months": "3 oy - 120,000 so'm",
        "payment_success": "To'lov muvaffaqiyatli amalga oshirildi! Sizga Premium obuna berildi.",
        
        # Workout
        "btn_workout": "🏋️‍♂️ Mashqlar rejasi",
        "btn_meal": "🍏 Ovqatlanish rejasi",
        "choose_plan_type": "Qaysi reja kerak?",
        "generating_plan": "⏳ AI reja tuzmoqda...",
        
        # Errors
        "error_generic": "❌ Xatolik yuz berdi.",
        "error_number": "❌ Iltimos, raqam kiriting.",
    },
    "ru": {
        # ... (existing) ...
        # Premium
        "premium_title": "💎 **Премиум Подписка**",
        "premium_desc": "С Премиум подпиской вы получаете:\n\n✅ Индивидуальный AI план тренировок\n✅ Индивидуальный AI план питания\n✅ Безлимитные запросы\n✅ Быстрая поддержка",
        "buy_1_month": "1 месяц - 50,000 сум",
        "buy_3_months": "3 месяца - 120,000 сум",
        "payment_success": "Оплата прошла успешно! Вам выдана Премиум подписка.",
        
        # Workout
        "btn_workout": "🏋️‍♂️ План тренировок",
        "btn_meal": "🍏 План питания",
        "choose_plan_type": "Какой план вам нужен?",
        "generating_plan": "⏳ AI составляет план...",
        
        # Errors
        "error_generic": "❌ Произошла ошибка.",
        "error_number": "❌ Пожалуйста, введите число.",
    },
    "en": {
        # ... (existing) ...
        # Premium
        "premium_title": "💎 **Premium Subscription**",
        "premium_desc": "With Premium subscription you get:\n\n✅ Individual AI workout plan\n✅ Individual AI meal plan\n✅ Unlimited requests\n✅ Fast support",
        "buy_1_month": "1 month - 50,000 UZS",
        "buy_3_months": "3 months - 120,000 UZS",
        "payment_success": "Payment successful! You have been granted Premium subscription.",
        
        # Workout
        "btn_workout": "🏋️‍♂️ Workout Plan",
        "btn_meal": "🍏 Meal Plan",
        "choose_plan_type": "Which plan do you need?",
        "generating_plan": "⏳ AI is generating plan...",
        
        # Errors
        "error_generic": "❌ An error occurred.",
        "error_number": "❌ Please enter a number.",
    }
}
}

def get_text(key, lang="uz", **kwargs):
    """Get translated text by key and language code."""
    text = TRANS.get(lang, TRANS["uz"]).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
