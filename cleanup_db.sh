#!/bin/bash
# Database cleanup script

echo "🗑️  Ma'lumotlar bazasini tozalash..."

# Remove all database files
rm -f fitness_bot.db yasha.db *.db

echo "✅ Barcha .db fayllar o'chirildi"
echo ""
echo "📝 Yangi ma'lumotlar bazasi avtomatik yaratiladi:"
echo "   - Bot yoki Backend birinchi ishga tushganda"
echo "   - Barcha jadvallar bo'sh holatda yaratiladi"
echo ""
echo "🔄 Botni qayta ishga tushiring: python bot_runner.py"
