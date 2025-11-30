import unittest
from unittest.mock import MagicMock, patch
from bot.calories import handle_calorie_button, handle_food_photo, STATE_CALORIE_PHOTO
from bot.onboarding import OnboardingManager
from datetime import datetime, timedelta

class TestCalorieFeature(unittest.TestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.manager = OnboardingManager()
        self.user_id = 12345
        self.message = MagicMock()
        self.message.from_user.id = self.user_id
        self.message.chat.id = self.user_id

    @patch('bot.calories.db')
    def test_premium_check_fail(self, mock_db):
        # User is not premium
        mock_db.get_user.return_value = {'premium_until': None}
        
        handle_calorie_button(self.message, self.bot, self.manager)
        
        # Should send premium offer
        self.bot.send_message.assert_called()
        args, kwargs = self.bot.send_message.call_args
        self.assertIn("faqat Premium", args[1])

    @patch('bot.calories.db')
    def test_premium_check_success(self, mock_db):
        # User is premium
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        mock_db.get_user.return_value = {'premium_until': future_date}
        
        handle_calorie_button(self.message, self.bot, self.manager)
        
        # Should set state and ask for photo
        self.assertEqual(self.manager.get_state(self.user_id), STATE_CALORIE_PHOTO)
        self.bot.send_message.assert_called()
        args, kwargs = self.bot.send_message.call_args
        self.assertIn("Ovqat rasmini yuboring", args[1])

    @patch('bot.calories.analyze_food_image')
    @patch('bot.calories.db')
    def test_photo_processing(self, mock_db, mock_analyze):
        # Setup state
        self.manager.set_state(self.user_id, STATE_CALORIE_PHOTO)
        
        # Mock photo
        self.message.photo = [MagicMock()]
        self.bot.get_file.return_value.file_path = "path/to/photo.jpg"
        self.bot.download_file.return_value = b"fake_image_data"
        
        # Mock AI response
        mock_analyze.return_value = '{"items": [{"name": "Apple", "grams": 100, "calories": 52}], "total_calories": 52}'
        
        handle_food_photo(self.message, self.bot, self.manager)
        
        # Should edit message with result
        self.bot.edit_message_text.assert_called()
        args, kwargs = self.bot.edit_message_text.call_args
        self.assertIn("Apple", args[0])
        self.assertIn("52 kcal", args[0])
        
        # Should log to DB
        mock_db.log_calorie_check.assert_called_with(self.user_id, 52, mock_analyze.return_value)
        
        # Should reset state
        self.assertEqual(self.manager.get_state(self.user_id), 0)

if __name__ == '__main__':
    unittest.main()
