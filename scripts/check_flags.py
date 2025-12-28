from core.db import db
from core.flags import is_flag_enabled

def check_and_fix():
    print("Checking 'coach_zone' flag...")
    flag = db.get_feature_flag("coach_zone")
    if not flag:
        print("Flag missing. Creating and enabling...")
        db.set_feature_flag("coach_zone", True, rollout_percent=100)
    else:
        print(f"Flag found: {flag}")
        if not flag['enabled'] or flag['rollout_percent'] < 100:
            print("Enabling flag and setting rollout to 100%...")
            db.set_feature_flag("coach_zone", True, rollout_percent=100)
    
    # Verify
    enabled = is_flag_enabled("coach_zone")
    print(f"Final status: {'ENABLED' if enabled else 'DISABLED'}")

if __name__ == "__main__":
    check_and_fix()
