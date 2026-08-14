"""Public AI-knowledge quiz — backend for the Instagram-bio landing page
(landing-quiz/). Each profession has its own 20-question bank; a random 6
are served per visit, scored server-side, and the full response set is
stored along with contact info. Hands back a Telegram deep link that
continues the flow in the bot.
"""
import random
import re
import secrets
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from bot.config import settings
from db.database import async_session
from db.models import QuizEvent, QuizSubmission

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

PROFESSIONS = {"biznes_egasi", "oqituvchi", "oquvchi", "mutaxassis", "shifokor", "ijodkor"}
EVENT_TYPES = {"page_view", "profession_selected", "quiz_started", "quiz_completed", "contact_view", "submitted"}
QUESTIONS_PER_QUIZ = 6


# ── Question bank ──────────────────────────────────────────────────────────
# Each entry: (question_text, correct_answer_text, [wrong1, wrong2, wrong3]).
# The correct answer's position is rotated deterministically at load time
# (not always option A) — see _build_bank().
_RAW_BANK = {
    "biznes_egasi": [
        ("ChatGPT — bu nima?", "Sun'iy intellekt bilan yozishib gaplashish mumkin bo'lgan dastur", ["Qidiruv tizimi", "Bank ilovasi", "Reklama platformasi"]),
        ("Zapier yoki Make kabi vositalar nima uchun ishlatiladi?", "Turli ilovalar orasida avtomatik jarayon (workflow) yaratish uchun", ["Video tahrirlash uchun", "Fayl siqish uchun", "Parol saqlash uchun"]),
        ("AI orqali mijozlarga avtomatik javob beradigan tizim odatda nima deb ataladi?", "Chatbot", ["Kalkulyator", "Antivirus", "Brauzer"]),
        ("Biznesda AI'dan qaysi sohada ko'proq foydalaniladi?", "Marketing kontenti va mijozlar bilan ishlash", ["Faqat buxgalteriya", "Faqat yuk tashish", "Hech qaysi sohada foydalanib bo'lmaydi"]),
        ("AI yordamida ijtimoiy tarmoq postlarini...", "Tezroq va ko'proq variantda tayyorlash mumkin", ["Umuman tayyorlab bo'lmaydi", "Faqat rasm chizish mumkin", "Faqat dasturchilar tayyorlay oladi"]),
        ("CRM tizimiga AI qo'shilsa, biznes uchun asosiy foyda nima?", "Mijozlar bilan aloqani va ma'lumotlarni avtomatik tahlil qilish", ["Ofis ijarasini arzonlashtirish", "Internetni tezlashtirish", "Soliqni kamaytirish"]),
        ("AI'dan foydalanib narx strategiyasini tahlil qilishda nimaga e'tibor berish kerak?", "Natijani tekshirib, o'z bilim va tajribangiz bilan solishtirish", ["AI aytgan narxni tekshirmasdan qabul qilish", "Faqat AI'ga ishonish kifoya", "Bunga umuman ehtiyoj yo'q"]),
        ("Quyidagilardan qaysi biri AI orqali reklama banner/rasm yaratadi?", "Midjourney", ["1C", "Excel", "Zoom"]),
        ("AI yordamchisidan biznes-reja tuzishda foydalanish...", "Vaqtni tejaydi, lekin yakuniy qarorni siz qabul qilishingiz kerak", ["Butunlay AI qaror qabul qiladi", "Foydasiz", "Faqat katta kompaniyalar uchun mo'ljallangan"]),
        ("Quyidagilardan qaysi biri \"AI xodim\" (virtual yordamchi) vazifasiga misol bo'la oladi?", "Mijozlarning tez-tez so'raladigan savollariga avtomatik javob berish", ["Ofisni tozalash", "Yuk mashinasini haydash", "Binoni qurish"]),
        ("Kichik biznes uchun AI'dan foydalanish qimmatga tushadimi?", "Ko'p AI vositalarning bepul yoki arzon tariflari mavjud", ["Har doim juda qimmat", "Faqat davlat korxonalari ishlata oladi", "Faqat IT kompaniyalar uchun"]),
        ("AI yordamida email yozishning afzalligi nima?", "Tez va grammatik xatosiz matn tayyorlash", ["Email umuman yuborilmaydi", "Faqat ingliz tilida ishlaydi", "Xavfsizlikni kamaytiradi"]),
        ("\"Sun'iy intellekt orqali tahlil\" deganda odatda nima nazarda tutiladi?", "Katta hajmdagi ma'lumotdan xulosa va tendensiyalarni topish", ["Faqat rasmlarni ranglash", "Faqat musiqa yozish", "Faqat o'yin yaratish"]),
        ("Mijozlar sharhlarini AI yordamida tahlil qilish nima beradi?", "Umumiy kayfiyat va muammoli joylarni tezda aniqlash", ["Hech qanday foyda bermaydi", "Faqat sharhlarni o'chiradi", "Mijozlarni avtomatik bloklaydi"]),
        ("AI asosidagi tarjima vositalari qanday ishlatiladi?", "Xorijiy mijozlar bilan tezroq muloqot qilish uchun", ["Faqat filmlarni tarjima qilish uchun", "Faqat davlat idoralarida", "Ular ishlatilmaydi"]),
        ("Sun'iy intellekt yordamida logotip yoki dizayn g'oyalarini...", "Tez taklif sifatida olish mumkin, keyin dizayner bilan yakunlash tavsiya etiladi", ["Umuman olib bo'lmaydi", "Faqat professional dizaynerlar oladi", "Faqat pullik dasturlarda mumkin"]),
        ("Quyidagilardan qaysi biri AI orqali matndan ovoz yaratadigan xizmat turi?", "Text-to-Speech (matndan ovoz) xizmatlari", ["Excel", "Faqat Photoshop", "Bunday texnologiya yo'q"]),
        ("Biznesda AI qarorlarini tekshirmasdan 100% ishonib amalga oshirish nima uchun xavfli?", "AI ba'zan noto'g'ri yoki eskirgan ma'lumot berishi mumkin", ["AI hech qachon xato qilmaydi", "Bu xavfli emas", "AI hamma narsani biladi"]),
        ("AI yordamida raqobatchilar tahlilini tezlashtirish mumkinmi?", "Ha, ochiq ma'lumotlarni tezroq yig'ib, tuzib berishi mumkin", ["Yo'q, bu imkonsiz", "Faqat sud orqali mumkin", "Faqat davlat ruxsati bilan"]),
        ("Kichik biznes egasi AI'ni qayerdan o'rganishi mumkin?", "Onlayn bepul darslar va amaliy sinab ko'rish orqali", ["Faqat universitetda", "Buni o'rganib bo'lmaydi", "Faqat xorijda"]),
    ],
    "oqituvchi": [
        ("ChatGPT — bu nima?", "AI bilan yozishib gaplashish mumkin bo'lgan dastur", ["Elektron kundalik", "Video darslik platformasi", "Testlar bazasi"]),
        ("AI o'qituvchiga dars ishlanmasi tuzishda qanday yordam beradi?", "Tez qoralama va g'oyalar taklif qiladi, o'qituvchi tekshirib to'ldiradi", ["Darsni o'qituvchisiz o'zi o'tadi", "Faqat testlar chop etadi", "Hech qanday yordam bermaydi"]),
        ("O'quvchi insho yozishda AI'dan foydalansa, bu qanday muammo tug'dirishi mumkin?", "O'z fikrini shakllantirish o'rniga tayyor matndan nusxa ko'chirishi mumkin", ["Hech qanday muammo yo'q", "Bu har doim foydali", "Bu taqiqlangan emas, muammosiz"]),
        ("AI yordamida testlar va topshiriqlarni tezroq tuzish mumkinmi?", "Ha, savollar bankini tezroq shakllantirish mumkin", ["Yo'q, bu imkonsiz", "Faqat matematika uchun mumkin", "Faqat chet tili uchun mumkin"]),
        ("AI asosidagi platformalar o'quvchining bilim darajasiga qarab...", "Shaxsiylashtirilgan mashqlar taklif qilishi mumkin", ["Hech narsa qila olmaydi", "Faqat baho qo'yadi", "Faqat davomatni yozadi"]),
        ("O'qituvchi AI yozgan matnni tekshirmasdan sinfga bersa nima xavf bor?", "Matnda xato yoki noaniq ma'lumot bo'lishi mumkin", ["Hech qanday xavf yo'q", "AI hech qachon xato qilmaydi", "Bu eng ishonchli manba"]),
        ("Plagiatni aniqlashda AI vositalari...", "Matnlarni solishtirib, o'xshashlikni aniqlashga yordam beradi", ["Hech narsa qila olmaydi", "Faqat rasmlar uchun ishlaydi", "Faqat pullik maktablarda mavjud"]),
        ("Quyidagilardan qaysi biri ta'limda AI'dan foydalanishning to'g'ri usuli?", "Tushunmagan mavzuni sodda tilda qayta tushuntirishni so'rash", ["Uy vazifasini butunlay AI'ga yozdirib, o'zi o'rganmaslik", "Imtihonda yashirincha AI'dan javob olish", "Boshqalarning ishini AI orqali ko'chirish"]),
        ("AI yordamida taqdimot tayyorlash imkoniyati bormi?", "Ha, matn va tuzilma bo'yicha g'oyalar berishi mumkin", ["Yo'q, bu texnik jihatdan imkonsiz", "Faqat rasm chizadi, matn yoza olmaydi", "Faqat video yaratadi"]),
        ("O'qituvchilar uchun AI'ning eng katta foydasi nima?", "Takrorlanuvchi ishlarga sarflanadigan vaqtni qisqartirish", ["Maoshni oshirish", "Sinfni kattalashtirish", "Ta'til kunlarini ko'paytirish"]),
        ("AI chatbot bilan til o'rganish mumkinmi?", "Ha, suhbat mashqlari qilish uchun foydalanish mumkin", ["Yo'q, faqat o'qituvchi bilan mumkin", "Faqat kattalar uchun", "Bu foydasiz"]),
        ("Sun'iy intellekt baho qo'yishda o'qituvchini to'liq almashtirishi kerakmi?", "Yo'q, u yordamchi vosita, yakuniy qaror o'qituvchida qolishi kerak", ["Ha, butunlay almashtirishi kerak", "Bu shart emas, chunki AI hamma narsani biladi", "Bu qonun bilan majburiy"]),
        ("AI orqali interaktiv testlar yaratish mumkinmi?", "Ha, savol va variantlarni tez generatsiya qilish mumkin", ["Yo'q", "Faqat dasturchilar yarata oladi", "Faqat xorijiy maktablarda"]),
        ("O'quvchilarga AI vositalaridan foydalanishni o'rgatish nima uchun muhim?", "Kelajakda ishda va o'qishda AI keng qo'llaniladi", ["Bu shart emas", "Bu foydasiz mashg'ulot", "Faqat dasturchilarga kerak"]),
        ("AI'dan foydalanib ota-onalarga hisobot yozishda nima e'tiborga olinishi kerak?", "Ma'lumotlarning to'g'riligini tekshirish", ["Hech narsani tekshirmaslik", "Faqat AI aytganini yuborish", "Bunga ehtiyoj yo'q"]),
        ("Quyidagilardan qaysi biri AI orqali video-dars yaratishga yordam beradigan vosita turi?", "Matndan taqdimot/video generatorlar", ["Faqat qog'oz va qalam", "Faqat proyektor", "Faqat doska"]),
        ("AI yordamida bir mavzuni turli darajadagi o'quvchilar uchun qayta yozish mumkinmi?", "Ha, matn darajasini moslashtirish mumkin", ["Yo'q", "Faqat rasm bilan mumkin", "Faqat video bilan mumkin"]),
        ("Maktabda AI ishlatish siyosati nega kerak?", "To'g'ri va noto'g'ri foydalanish chegarasini aniq belgilash uchun", ["Kerak emas, chunki AI taqiqlangan", "Faqat texnik xodimlar uchun kerak", "Bu davlat siri"]),
        ("AI orqali test natijalarini tezroq tahlil qilish nima beradi?", "Qaysi mavzular qiyinligini tezroq aniqlashga yordam beradi", ["Foydasiz", "Faqat vaqt yo'qotadi", "Faqat matematika uchun ishlaydi"]),
        ("O'qituvchi AI'dan foydalanganda eng muhimi nimani unutmaslik?", "Tanqidiy fikrlash va tekshirishni", ["Internetni o'chirishni", "Kompyuterni yangilashni", "Elektr energiyasini tejashni"]),
    ],
    "oquvchi": [
        ("ChatGPT — bu nima?", "AI bilan yozishib gaplashish mumkin bo'lgan dastur", ["Elektron kutubxona", "Ijtimoiy tarmoq", "O'yin platformasi"]),
        ("Uy vazifasini AI'ga to'liq yozdirib, tushunmasdan topshirish to'g'rimi?", "Yo'q, bu o'rganishga to'sqinlik qiladi", ["Ha, bu eng yaxshi usul", "Bu har doim ruxsat etilgan", "Farqi yo'q"]),
        ("AI'dan mavzuni tushunmay qolganda qanday foydalanish mumkin?", "Sodda tilda qayta tushuntirib berishni so'rash", ["Faqat javobni ko'chirib olish", "Undan foydalanish mumkin emas", "Faqat rasm chizdirish"]),
        ("AI berilgan javob har doim 100% to'g'rimi?", "Yo'q, ba'zan xato yoki noaniq bo'lishi mumkin", ["Ha, hech qachon xato qilmaydi", "Faqat matematikada xato qiladi", "Faqat kechqurun ishlamaydi"]),
        ("Referat yoki insho yozishda AI'dan qanday foydalanish foydali?", "G'oya va reja tuzishda yordamchi sifatida", ["To'liq nusxasini o'z nomidan topshirish uchun", "Imtihonda yashirincha ishlatish uchun", "Bunday foydalanish yo'q"]),
        ("Sun'iy intellekt yordamida chet tilini mashq qilish mumkinmi?", "Ha, suhbat va yozish mashqlari qilish mumkin", ["Yo'q", "Faqat maktabda mumkin", "Faqat kattalar uchun"]),
        ("Prompt qanday bo'lsa yaxshiroq javob olinadi?", "Aniq va batafsil yozilsa", ["Juda qisqa, bitta so'z bilan", "Farqi yo'q, natija bir xil", "Faqat ingliz tilida yozilsa"]),
        ("AI yordamida matematik masalani yechishda nimaga e'tibor berish kerak?", "Yechim yo'lini tushunib, o'zingiz ham qayta yechib ko'rish", ["Faqat javobni yozib qo'yish", "Hisoblashni umuman o'rganmaslik", "Bunga ehtiyoj yo'q"]),
        ("AI'dan olingan ma'lumotni tekshirmasdan ishlatish nima uchun xavfli?", "Ma'lumot noto'g'ri yoki eskirgan bo'lishi mumkin", ["Hech qanday xavf yo'q", "Bu har doim to'g'ri bo'ladi", "Faqat internetda xavf bor, AI'da yo'q"]),
        ("AI'dan referat mavzusini tanlashda foydalanish mumkinmi?", "Ha, g'oyalar va mavzular ro'yxatini so'rash mumkin", ["Yo'q", "Faqat o'qituvchi tanlashi kerak", "Bu qonunga zid"]),
        ("Imtihonda yashirincha AI ishlatish nima uchun noto'g'ri?", "Bu aldov hisoblanadi va bilimni real baholashga xalaqit beradi", ["Bu ruxsat etilgan", "Hech qanday muammo yo'q", "Bu faqat qulaylik"]),
        ("AI yordamida dasturlash o'rganish mumkinmi?", "Ha, misollar va tushuntirishlar olish orqali", ["Yo'q", "Faqat universitetda mumkin", "Faqat kattalar uchun"]),
        ("Sun'iy intellekt bir xil savolga har safar bir xil javob beradimi?", "Yo'q, javob har safar biroz farqli bo'lishi mumkin", ["Ha, doim so'zma-so'z bir xil", "Ikkinchi marta ishlamaydi", "Faqat birinchi savolga javob beradi"]),
        ("Quyidagilardan qaysi biri AI orqali rasm chizadigan dastur?", "Midjourney", ["Word", "Kalkulyator", "Telegram"]),
        ("O'quvchi uchun AI'dan foydalanishning eng foydali tomoni nima?", "Tushunmagan narsani istalgan vaqtda so'rab, tez tushunish", ["Uy vazifasini butunlay o'rniga bajarishi", "Darsga qatnashmaslik imkoni", "Kitob o'qimaslik imkoni"]),
        ("Aniq va batafsil so'rov yozish nima uchun muhim?", "Ikkinchisi aniqroq bo'lgani uchun yaxshiroq javob beradi", ["Farqi yo'q", "Birinchisi har doim yaxshiroq", "AI ikkalasini ham tushunmaydi"]),
        ("AI yordamida loyihaga rasm/slayd tayyorlash mumkinmi?", "Ha, g'oya va dizayn taklif qilishi mumkin", ["Yo'q", "Faqat pullik dasturlarda", "Faqat kattalar uchun"]),
        ("Do'stlar bilan AI haqida gaplashganda eng muhim narsa nima?", "Uni qanday to'g'ri va halol foydalanish mumkinligini muhokama qilish", ["Faqat o'yin haqida gapirish", "AI haqida gapirmaslik kerak", "Faqat kim ko'proq ishlatganini maqtanish"]),
        ("AI sizga noto'g'ri yoki g'alati javob bersa nima qilish kerak?", "Boshqa manbalar bilan tekshirish yoki qayta so'rash", ["Darhol ishonib qabul qilish", "Hech narsa qilmaslik kerak", "AI'ni butunlay tark etish"]),
        ("Kelajakda ko'p kasblarda AI bilimi nima uchun foydali bo'ladi?", "Chunki ko'p sohalarda AI vositalari qo'llanilmoqda", ["Chunki AI hamma kasblarni yo'q qiladi", "Bunga hech qachon ehtiyoj bo'lmaydi", "Faqat dasturchilarga kerak bo'ladi"]),
    ],
    "mutaxassis": [
        ("ChatGPT — bu nima?", "AI bilan yozishib gaplashish mumkin bo'lgan dastur", ["Buxgalteriya dasturi", "Elektron pochta xizmati", "Fayl arxivatori"]),
        ("AI'dan yaxshi natija olish uchun eng muhimi nima?", "Savolni aniq va batafsil yozish", ["Faqat bitta so'z yozish", "Qanday yozsangiz ham natija bir xil", "Faqat ingliz tilida yozish shart"]),
        ("AI har doim 100% to'g'ri javob beradimi?", "Yo'q, ba'zan noto'g'ri yoki noaniq ma'lumot berishi mumkin", ["Ha, hech qachon adashmaydi", "Faqat matematik savollarda adashadi", "Faqat kechqurun ishlamaydi"]),
        ("Quyidagilardan qaysi biri matndan rasm yaratadigan AI dastur?", "Midjourney", ["Excel", "Telegram", "Kalkulyator"]),
        ("Bir xil savolni AI'ga ikki marta bersangiz, nima bo'ladi?", "Javob har safar biroz farqli bo'lishi mumkin", ["Javob har doim so'zma-so'z bir xil chiqadi", "Ikkinchi marta AI ishlamay qoladi", "Faqat birinchi savolga javob beradi"]),
        ("Zapier yoki Make kabi vositalar AI bilan birga nima uchun ishlatiladi?", "Turli ilovalar orasida avtomatik jarayon yaratish uchun", ["Video tahrirlash uchun", "Fayllarni siqish uchun", "Parol saqlash uchun"]),
        ("Ish joyida AI'dan hisobot yozishda foydalanish nimaga yordam beradi?", "Vaqtni tejash va qoralama tayyorlash", ["Ishni butunlay o'rniga bajarish", "Hech qanday yordam bermaydi", "Faqat rasmiy hujjatlarga taqiqlangan"]),
        ("\"Prompt\" so'zi nimani anglatadi?", "AI'ga yozadigan savol yoki buyrug'ingiz", ["Kompyuter virusi", "Internet tezligi", "Parol"]),
        ("AI yordamida email yozish qanday foyda beradi?", "Tez va grammatik toza matn tayyorlash", ["Email umuman yuborilmaydi", "Faqat ingliz tilida ishlaydi", "Bu imkonsiz"]),
        ("AI'dan olingan ma'lumotni ishda ishlatishdan oldin nima qilish tavsiya etiladi?", "Tekshirib, ishonchli manba bilan solishtirish", ["Hech narsa qilmasdan ishlatish", "Faqat rangini o'zgartirish", "Hech qachon ishlatmaslik"]),
        ("AI orqali matnni boshqa tilga tarjima qilish sifati qanday?", "Ancha yaxshi, lekin ba'zan tekshirish kerak", ["Har doim 100% mukammal", "Umuman ishlamaydi", "Faqat bitta til juftligida ishlaydi"]),
        ("Ofis ishlarida AI'dan foydalanishning asosiy maqsadi nima?", "Takrorlanuvchi vazifalarga sarflanadigan vaqtni kamaytirish", ["Xodimlarni butunlay almashtirish", "Internetni sekinlashtirish", "Hech qanday maqsadi yo'q"]),
        ("AI yordamida hisobot uchun matn tuzilmasini tezroq yaratish mumkinmi?", "Ha, mumkin", ["Yo'q, imkonsiz", "Faqat dizaynerlar uchun", "Faqat kattalar uchun"]),
        ("AI tizimlariga maxfiy ma'lumot kiritishda nimaga e'tibor berish kerak?", "Maxfiylik siyosatini bilish va ehtiyot bo'lish", ["Hech qanday cheklov yo'q", "Har doim hamma narsani kiritsa bo'ladi", "Bu masala umuman muhim emas"]),
        ("AI chatbotlar mijozlar xizmatida qanday rol o'ynaydi?", "Tez-tez so'raladigan savollarga tezkor javob berish", ["Faqat o'yin o'ynatadi", "Hech qanday rol o'ynamaydi", "Faqat pul o'tkazadi"]),
        ("Ishda AI vositasini tanlashda nimaga e'tibor berish kerak?", "Vazifaga mosligi va ishonchliligi", ["Faqat nomi chiroyli bo'lishi", "Faqat bepul bo'lishi", "Farqi yo'q, hammasi bir xil"]),
        ("AI orqali ma'lumotlarni jadval yoki diagrammaga aylantirish mumkinmi?", "Ha, matnni tuzilmali formatga keltirish mumkin", ["Yo'q", "Faqat dasturchilar qila oladi", "Faqat qog'ozda mumkin"]),
        ("Kasbiy rivojlanish uchun AI vositalarini o'rganish nima uchun foydali?", "Ko'p sohalarda ish samaradorligini oshiradi", ["Hech qanday foydasi yo'q", "Faqat IT sohasida kerak", "Bu vaqt yo'qotish"]),
        ("AI'dan olingan g'oyani ishda qo'llashdan oldin nima qilish kerak?", "O'z tajribangiz va kontekstga moslashtirib ko'rib chiqish", ["Hech narsa o'zgartirmasdan qo'llash", "Umuman e'tiborsiz qoldirish", "Faqat rahbarga ko'rsatmasdan qo'llash"]),
        ("Sun'iy intellekt bilan ishlashda eng muhim ko'nikma nima?", "Aniq topshiriq bera olish va natijani tanqidiy baholash", ["Faqat tez yozish", "Faqat ingliz tilini bilish", "Faqat kompyuter tuzilishini bilish"]),
    ],
    "shifokor": [
        ("ChatGPT — bu nima?", "AI bilan yozishib gaplashish mumkin bo'lgan dastur", ["Tibbiy asboblar do'koni", "Retsept yozish tizimi", "Kasalxona nomi"]),
        ("Tibbiyotda AI qaror qabul qilishda shifokorni to'liq almashtira oladimi?", "Yo'q, u yordamchi vosita, yakuniy qaror shifokorda qolishi kerak", ["Ha, butunlay almashtiradi", "Bu qonun bilan majburiy", "Bu allaqachon sodir bo'lgan"]),
        ("AI yordamida tibbiy tasvirlarni tahlil qilish nima uchun foydali bo'lishi mumkin?", "Shubhali joylarni tezroq aniqlashga yordam berishi mumkin", ["Diagnozni 100% aniq qo'yadi", "Shifokor ishini butunlay bekor qiladi", "Hech qanday foydasi yo'q"]),
        ("Bemor ma'lumotlarini AI tizimlariga kiritishda nimaga alohida e'tibor berish kerak?", "Maxfiylik va shaxsiy ma'lumotlar xavfsizligiga", ["Hech narsaga, cheklov yo'q", "Faqat internet tezligiga", "Faqat dastur rangiga"]),
        ("AI'dan olingan tibbiy ma'lumotni tekshirmasdan bemorga qo'llash to'g'rimi?", "Yo'q, professional tekshiruv va tajriba shart", ["Ha, har doim to'g'ri", "Bu tavsiya etiladi", "Farqi yo'q"]),
        ("Sun'iy intellekt dori-darmon o'zaro ta'sirini tekshirishda qanday yordam berishi mumkin?", "Ma'lumotlar bazasidan tezroq mos kelmasliklarni topishga yordam beradi", ["Hech qanday yordam bermaydi", "Dorini avtomatik retseptga yozadi", "Faqat narxni hisoblaydi"]),
        ("AI yordamida tibbiy hujjatlar yozishda vaqtni tejash mumkinmi?", "Ha, qoralama tayyorlashda yordam beradi", ["Yo'q", "Faqat qo'lda yozish kerak", "Bu taqiqlangan"]),
        ("Bemorlar AI chatbotidan sog'liq haqida maslahat olganda nimani unutmasligi kerak?", "Jiddiy holatda albatta shifokorga murojaat qilish kerakligini", ["AI shifokordan yaxshiroq ekanini", "Shifokorga borish shart emasligini", "AI hech qachon xato qilmasligini"]),
        ("Tibbiy ta'limda AI vositalari qanday ishlatilishi mumkin?", "Murakkab mavzularni tushuntirish va testlar tayyorlashda", ["Amaliyotni butunlay almashtirishda", "Hech qanday foyda yo'q", "Faqat imtihon topshirishda"]),
        ("AI diagnostika tizimi noto'g'ri natija bersa, kim javobgar bo'ladi?", "Yakuniy qarorni qabul qilgan shifokor", ["Faqat dastur ishlab chiquvchisi", "Hech kim javobgar emas", "Bemorning o'zi"]),
        ("Sun'iy intellekt yordamida ilmiy tibbiy maqolalarni qidirish mumkinmi?", "Ha, mumkin", ["Yo'q", "Faqat ingliz tilida imkonsiz", "Faqat pullik xizmatlarda"]),
        ("Bemor tarixini yuritishda AI yordamida avtomatlashtirish nima beradi?", "Ma'lumotlarni tezroq va tartibli saqlash", ["Hech qanday foyda", "Bemor ma'lumotlarini yo'qotadi", "Faqat qog'ozni ko'paytiradi"]),
        ("AI asosidagi kiyiladigan qurilmalar (masalan soat) nimani kuzatishi mumkin?", "Yurak urishi va faollik ko'rsatkichlarini", ["Faqat vaqtni", "Faqat qadam sonini emas, hech narsani", "Hech narsa kuzata olmaydi"]),
        ("Shifokor AI tavsiyasiga shubha qilsa nima qilishi kerak?", "O'z klinik bilimi va qo'shimcha tekshiruvlarga tayanishi", ["Har doim AI'ga ishonishi", "Bemorni davolashni to'xtatishi", "AI'ni butunlay o'chirib tashlashi"]),
        ("Sun'iy intellekt tibbiyotda qaysi jarayonni tezlashtirishga yordam berishi mumkin?", "Katta hajmdagi tibbiy ma'lumotlarni tahlil qilish", ["Operatsiyani shifokorsiz bajarish", "Dori ishlab chiqarishni bekor qilish", "Bemorlarni davolashni to'xtatish"]),
        ("AI yordamida bemorlarga dori ichish vaqti haqida eslatma yuborish tizimlari mavjudmi?", "Ha, mavjud", ["Yo'q", "Faqat kasalxonada mavjud", "Faqat davlat dasturlarida"]),
        ("Tibbiy AI vositalarini qo'llashdan oldin ular qanday tekshiruvdan o'tishi kerak?", "Klinik sinov va tasdiqlashdan", ["Hech qanday tekshiruv shart emas", "Faqat dasturchi tekshiruvidan", "Faqat bemor roziligidan"]),
        ("Simptom-checker vositalari nima uchun ehtiyotkorlik bilan ishlatilishi kerak?", "Ular aniq diagnoz emas, faqat dastlabki yo'naltirish beradi", ["Ular har doim 100% aniq diagnoz qo'yadi", "Ularga umuman ishonib bo'lmaydi", "Ular shifokorni butunlay almashtiradi"]),
        ("Sog'liqni saqlashda AI ma'lumotlar maxfiyligi nima uchun muhim?", "Bemor shaxsiy ma'lumotlari noto'g'ri qo'llardan himoyalanishi kerak", ["Bu muhim emas", "Faqat davlat kasalxonalarida muhim", "Faqat xorijda muhim"]),
        ("Shifokor uchun AI'ni o'rganishning asosiy foydasi nima?", "Kundalik ishda vaqtni tejab, bemorga ko'proq e'tibor qaratish", ["Bemorlar bilan gaplashishni kamaytirish", "Ish haqini kamaytirish", "Diplomni bekor qilish"]),
    ],
    "ijodkor": [
        ("ChatGPT — bu nima?", "AI bilan yozishib gaplashish mumkin bo'lgan dastur", ["Musiqa pleyeri", "Foto redaktor nomi", "Ijtimoiy tarmoq"]),
        ("Quyidagilardan qaysi biri matndan rasm yaratadigan AI dastur?", "Midjourney", ["Excel", "Kalkulyator", "Telegram"]),
        ("AI yordamida musiqa yaratish mumkinmi?", "Ha, maxsus AI vositalari mavjud", ["Yo'q, bu imkonsiz", "Faqat professional studiyalarda", "Faqat instrumental musiqa uchun"]),
        ("AI orqali yaratilgan asarning mualliflik huquqi masalasi qanday?", "Hali munozarali va mamlakatlarda turlicha qaraladi", ["Hech qachon muammo bo'lmaydi", "Har doim AI kompaniyasiga tegishli", "Bunday masala umuman yo'q"]),
        ("Ijodkor AI'dan g'oya olib, keyin o'z uslubida ishlab chiqishi...", "Yaxshi amaliyot hisoblanadi", ["Har doim taqiqlangan", "Hech qanday ma'no bermaydi", "Faqat kattalar uchun"]),
        ("Video tahrirlashda AI qanday yordam berishi mumkin?", "Avtomatik subtitr, ovoz tozalash va montaj taklif qilish", ["Hech qanday yordam bermaydi", "Faqat videoni o'chiradi", "Faqat rangini qora-oq qiladi"]),
        ("AI orqali yaratilgan kontentni belgilash nima uchun muhim bo'lishi mumkin?", "Auditoriyaga shaffoflik va ishonch uchun", ["Hech qanday ahamiyati yo'q", "Bu taqiqlangan", "Faqat qonun talab qilmasa kerak emas"]),
        ("Boshqa muallifning uslubini AI orqali aynan nusxalab, o'z nomingizdan taqdim etish...", "Odob-axloq va mualliflik huquqi nuqtai nazaridan noto'g'ri", ["Har doim ruxsat etilgan", "Bu ijodkorlik hisoblanadi", "Hech qanday muammo yo'q"]),
        ("AI yordamida logotip yoki brend dizayni g'oyalarini tez olish mumkinmi?", "Ha, dastlabki variantlar sifatida", ["Yo'q", "Faqat pullik dasturlarda", "Faqat kattalar uchun"]),
        ("Ijodiy blokka tushganda AI qanday yordam berishi mumkin?", "Yangi g'oya va yo'nalishlar taklif qilib", ["Hech qanday yordam bermaydi", "Faqat vaqtni yo'qotadi", "Ilhomni butunlay yo'qotadi"]),
        ("Matndan ovoz yaratadigan AI xizmati qanday nomlanadi?", "Ovoz sintezi (Text-to-Speech) vositalari", ["Faqat video pleyerlar", "Faqat rasm muharrirlari", "Bunday texnologiya yo'q"]),
        ("Fotosuratlarni AI yordamida sifatini oshirish (upscale) mumkinmi?", "Ha, mumkin", ["Yo'q", "Faqat professional kamerada olingan suratlar uchun", "Faqat qora-oq suratlar uchun"]),
        ("AI orqali yaratilgan qahramonni animatsiya qilish imkoniyati bormi?", "Ha, ba'zi vositalarda mavjud", ["Yo'q, umuman yo'q", "Faqat Hollywood studiyalarida", "Faqat 3D dasturchilar uchun"]),
        ("Ijodkor sifatida AI vositalaridan foydalanish uni \"haqiqiy ijodkor emas\" qiladimi?", "Yo'q, AI vosita, g'oya va tanlov ijodkorniki bo'lib qoladi", ["Ha, butunlay", "Bu munozarasiz aniq javob", "Faqat ba'zi mamlakatlarda"]),
        ("AI orqali ijtimoiy tarmoq uchun kontent-reja tuzish mumkinmi?", "Ha, mavzular va sanalar bo'yicha taklif berishi mumkin", ["Yo'q", "Faqat marketing agentliklari qila oladi", "Faqat pullik xizmatda"]),
        ("Rasm generatsiya qiluvchi AI'ga aniq va batafsil so'rov yozish nima uchun muhim?", "Xohlagan natijaga yaqinroq rasm olish uchun", ["Hech qanday ahamiyati yo'q", "Faqat uzunroq bo'lishi kifoya", "Bunga umuman ehtiyoj yo'q"]),
        ("AI bilan yaratilgan kontentni sotishda qanday masalaga e'tibor berish kerak?", "Har bir AI xizmatining o'z foydalanish shartlarini o'qib chiqish", ["Hech qanday shartga qarash shart emas", "Har doim bepul sotish mumkin", "Bu masala umuman yo'q"]),
        ("Video/rasm montajida AI orqali fonni almashtirish imkoniyati bormi?", "Ha, ko'plab vositalarda mavjud", ["Yo'q", "Faqat professional studiyada", "Faqat qimmat kompyuterda"]),
        ("Ijodkor AI natijasini qanday qabul qilishi maqsadga muvofiq?", "Boshlang'ich material/qoralama sifatida, keyin qayta ishlash", ["Har doim o'zgartirmasdan ishlatish kerak", "Umuman ishlatmaslik kerak", "Faqat mijozga ko'rsatmasdan yashirish"]),
        ("AI vositalarini o'rganish nima uchun zamonaviy ijodkor uchun foydali?", "Ish jarayonini tezlashtirib, yangi imkoniyatlar ochadi", ["Hech qanday foydasi yo'q", "Ijodkorlikni butunlay o'ldiradi", "Faqat texnik mutaxassislarga kerak"]),
    ],
}


def _build_bank():
    """Rotates the correct answer's position (0,1,2,3,...) per question so
    it's never always option A, then freezes the bank as a plain dict."""
    bank = {}
    for profession, items in _RAW_BANK.items():
        questions = []
        for i, (text, correct, wrongs) in enumerate(items):
            pos = i % 4
            options = wrongs[:pos] + [correct] + wrongs[pos:]
            questions.append({"text": text, "options": options, "correct": pos})
        bank[profession] = questions
    return bank


QUESTION_BANK = _build_bank()


# ── Schemas ──────────────────────────────────────────────────────────────
class QuizAnswer(BaseModel):
    question_index: int
    selected: int


class QuizSubmitRequest(BaseModel):
    profession: str
    answers: List[QuizAnswer]
    name: str
    phone: str
    session_id: Optional[str] = None
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name too short")
        return v[:255]

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v or "")
        if len(digits) < 9:
            raise ValueError("Invalid phone number")
        return v.strip()[:30]


class QuizEventRequest(BaseModel):
    session_id: str
    event_type: str
    utm_source: Optional[str] = ""
    utm_campaign: Optional[str] = ""


def _level_for(correct: int, total: int) -> str:
    if correct <= total * 0.34:
        return "boshlangich"
    if correct <= total * 0.67:
        return "orta"
    return "yuqori"


# ── Endpoints ────────────────────────────────────────────────────────────
@router.get("/questions")
async def get_quiz_questions(profession: str):
    """Returns a random 6-question subset for the given profession, without
    the correct answers. question_index refers to that profession's bank
    (0-19) — the client must echo it back on submit."""
    if profession not in QUESTION_BANK:
        raise HTTPException(status_code=400, detail="Unknown profession")

    bank = QUESTION_BANK[profession]
    indices = random.sample(range(len(bank)), QUESTIONS_PER_QUIZ)
    return {
        "profession": profession,
        "questions": [
            {"question_index": i, "text": bank[i]["text"], "options": bank[i]["options"]}
            for i in indices
        ],
    }


@router.post("/event")
async def track_quiz_event(payload: QuizEventRequest):
    """Fire-and-forget funnel tracking — never raises on bad input, just
    ignores it, since a broken analytics beacon must never break the quiz."""
    if payload.event_type not in EVENT_TYPES or not payload.session_id:
        return {"ok": True}

    async with async_session() as session:
        session.add(QuizEvent(
            session_id=payload.session_id[:64],
            event_type=payload.event_type,
            utm_source=(payload.utm_source or None),
            utm_campaign=(payload.utm_campaign or None),
        ))
        await session.commit()
    return {"ok": True}


@router.post("/submit")
async def submit_quiz(payload: QuizSubmitRequest):
    if payload.profession not in QUESTION_BANK:
        raise HTTPException(status_code=400, detail="Unknown profession")
    if len(payload.answers) != QUESTIONS_PER_QUIZ:
        raise HTTPException(status_code=400, detail="Invalid answers length")

    bank = QUESTION_BANK[payload.profession]
    correct = 0
    answers_out = []
    for a in payload.answers:
        if not (0 <= a.question_index < len(bank)) or not (0 <= a.selected <= 3):
            raise HTTPException(status_code=400, detail="Invalid answer")
        q = bank[a.question_index]
        is_correct = a.selected == q["correct"]
        correct += int(is_correct)
        answers_out.append({
            "question_index": a.question_index,
            "text": q["text"],
            "selected": q["options"][a.selected],
            "correct": is_correct,
        })

    level = _level_for(correct, QUESTIONS_PER_QUIZ)
    token = secrets.token_urlsafe(12)

    async with async_session() as session:
        session.add(QuizSubmission(
            token=token,
            answers=answers_out,
            correct_count=correct,
            level=level,
            profession=payload.profession,
            name=payload.name,
            phone=payload.phone,
            utm_source=payload.utm_source or None,
            utm_campaign=payload.utm_campaign or None,
        ))
        if payload.session_id:
            session.add(QuizEvent(
                session_id=payload.session_id[:64],
                event_type="submitted",
                utm_source=payload.utm_source or None,
                utm_campaign=payload.utm_campaign or None,
            ))
        await session.commit()

    redirect_url = f"https://t.me/{settings.BOT_USERNAME}?start=quiz_{token}"
    return {"token": token, "correct_count": correct, "level": level, "redirect_url": redirect_url}
