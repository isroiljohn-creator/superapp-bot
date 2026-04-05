"""FSM states for all bot flows."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationFSM(StatesGroup):
    """User registration flow — branched onboarding."""
    waiting_business_check = State()   # "Sizda biznes bormi?" → Ha / Yo'q
    waiting_business_need = State()    # Business owner: "Sizga nima kerak?"
    waiting_goal = State()             # Regular user: "Maqsadingiz?"
    waiting_level = State()            # Regular user: "Darajangiz?"
    waiting_name = State()
    waiting_age = State()
    waiting_phone = State()


class SegmentationFSM(StatesGroup):
    """Legacy segmentation — kept for backward compatibility."""
    waiting_goal = State()
    waiting_level = State()


class BroadcastFSM(StatesGroup):
    """Admin broadcast flow — bot-side compose + confirm."""
    waiting_content = State()
    waiting_confirm = State()


class ContentManagementFSM(StatesGroup):
    """Admin content management."""
    waiting_campaign = State()
    waiting_content_type = State()
    waiting_file = State()
    waiting_description = State()


class FunnelBuilderFSM(StatesGroup):
    """Admin funnel trigger builder."""
    waiting_event = State()
    waiting_condition = State()
    waiting_action = State()
    waiting_message = State()
    waiting_delay = State()


class JobPostFSM(StatesGroup):
    """Business owner job posting flow."""
    waiting_title = State()
    waiting_company = State()
    waiting_description = State()
    waiting_salary = State()
    waiting_job_type = State()
    waiting_location = State()
    waiting_contact = State()
    waiting_confirm = State()


class WalletTopUpFSM(StatesGroup):
    """User wallet top up amount flow."""
    waiting_for_amount = State()


class VideoNoteFSM(StatesGroup):
    """Circular video processing flow."""
    waiting_for_video = State()
