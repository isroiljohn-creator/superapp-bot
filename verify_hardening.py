
import os
import sys
import time
import threading
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

def test_wal_mode():
    print("--- Testing WAL Mode ---")
    try:
        from core.db import db
        from backend.database import sync_engine
        
        # Check journal mode
        with sync_engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA journal_mode")).fetchone()
            mode = result[0]
            print(f"Current Journal Mode: {mode}")
            
            if mode.upper() == "WAL":
                print("✅ WAL Mode Enabled")
            else:
                # Note: Might be 'memory' or 'delete' if not running against actual file or if init order differs.
                # But our code sets it on 'connect'.
                if "sqlite" in str(sync_engine.url):
                    print("⚠️ WAL Mode NOT detected (Might need file DB)")
                else:
                    print(f"ℹ️ Not using SQLite: {sync_engine.url}")
    except Exception as e:
        print(f"❌ DB Error: {e}")

def test_broadcast_threading():
    print("\n--- Testing Broadcast Threading ---")
    try:
        from bot import admin
        
        # Mock objects
        mock_bot = MagicMock()
        mock_message = MagicMock()
        mock_message.chat.id = 12345
        mock_message.text = "Test Broadcast"
        mock_message.content_type = 'text'
        
        # Patch _broadcast_worker to avoid actual DB calls/spam
        original_worker = admin._broadcast_worker
        
        worker_called = threading.Event()
        
        def mock_worker(message, bot, segment):
            print("🧵 Worker thread started!")
            time.sleep(0.5)
            print("🧵 Worker thread finished!")
            worker_called.set()
            
        admin._broadcast_worker = mock_worker
        
        print("🚀 Invoking process_broadcast...")
        start_time = time.time()
        admin.process_broadcast(mock_message, mock_bot, "all")
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱ Main thread return time: {duration:.4f}s")
        
        if duration < 0.1:
            print("✅ Main thread non-blocking")
        else:
            print("❌ Main thread BLOCKED")
            
        # Wait for worker
        worker_called.wait(timeout=2)
        if worker_called.is_set():
            print("✅ Worker thread executed")
        else:
            print("❌ Worker thread did not execute")
            
        # Restore
        admin._broadcast_worker = original_worker

    except Exception as e:
        print(f"❌ Broadcast Error: {e}")

def test_onboarding_validation():
    print("\n--- Testing Input Validation ---")
    try:
        from bot import onboarding
        
        # Mock Bot
        mock_bot = MagicMock()
        mock_bot.send_message = MagicMock()
        
        # Mock Manager
        onboarding.manager.get_state = MagicMock(return_value=onboarding.STATE_AGE)
        
        # 1. Test Sticker (Non-text)
        print("Testing Sticker Input for Age...")
        msg_sticker = MagicMock()
        msg_sticker.from_user.id = 111
        msg_sticker.content_type = 'sticker'
        msg_sticker.text = None
        
        onboarding.process_age(msg_sticker, mock_bot)
        
        # Verify strict error message
        args, _ = mock_bot.send_message.call_args
        if "matn" in args[1]:
            print("✅ Correctly rejected sticker with 'matn' warning")
        else:
            print(f"❌ Unexpected response: {args[1]}")
            
        # 2. Test Invalid Text
        print("Testing Invalid Text 'abc' for Age...")
        msg_text = MagicMock()
        msg_text.from_user.id = 111
        msg_text.content_type = 'text'
        msg_text.text = "abc"
        
        onboarding.process_age(msg_text, mock_bot)
         # Should trigger isdigit check
        args, _ = mock_bot.send_message.call_args
        if "raqamda" in args[1]:
             print("✅ Correctly rejected 'abc'")
        
    except Exception as e:
        print(f"❌ Input Validation Error: {e}")

if __name__ == "__main__":
    test_wal_mode()
    test_broadcast_threading()
    test_onboarding_validation()
