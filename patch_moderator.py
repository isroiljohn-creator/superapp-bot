import re

with open("bot/handlers/moderator.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace decorator
content = content.replace(
    '@router.callback_query(F.data == "superapp:moderator")\nasync def moderator_menu(callback: CallbackQuery, state: FSMContext):',
    '@router.message(F.text == uz.SUPERAPP_BTN_MODERATOR)\n@router.callback_query(F.data == "superapp:moderator")\nasync def moderator_menu(update: CallbackQuery | Message, state: FSMContext):\n    # If message, we just use from_user.id'
)

# And fix moderator_menu body:
content = content.replace(
    '    user_id = callback.from_user.id',
    '    user_id = update.from_user.id\n    bot_instance = update.bot\n    is_cb = isinstance(update, CallbackQuery)'
)
content = content.replace('bot_info = await callback.bot.get_me()', 'bot_info = await bot_instance.get_me()')
content = content.replace('await callback.message.edit_text(', 'await (update.message.edit_text if is_cb else update.answer)(')
content = content.replace('await callback.answer()', 'if is_cb:\n            await update.answer()')

with open("bot/handlers/moderator.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patched moderator.py")
