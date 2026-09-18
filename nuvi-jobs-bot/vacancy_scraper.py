import os
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilter

logger = logging.getLogger("jarvis.vacancy_scraper")

class VacancyScraper:
    """Telethon client dedicated to scraping vacancies from source channels."""
    
    def __init__(self, api_id: int, api_hash: str, session_string: str) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.connected = False
        
        session = StringSession(session_string)
        self.client = TelegramClient(session, api_id, api_hash)

    async def connect(self) -> None:
        """Connects and authorizes the scraper client."""
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.error("❌ Vacancy scraper Telegram session is NOT authorized.")
                self.connected = False
                return
            self.connected = True
            me = await self.client.get_me()
            logger.info(f"✅ Vacancy Scraper authorized successfully: @{me.username} ({me.first_name})")
        except Exception as e:
            logger.error(f"❌ Vacancy Scraper connection error: {e}")
            self.connected = False

    async def get_channels_from_folder(self, folder_name: str = "HR") -> list[int]:
        """Gets all channel/chat IDs inside a specified Telegram folder (filter)."""
        if not self.connected:
            return []
        try:
            r = await self.client(GetDialogFiltersRequest())
            for f in r.filters:
                if isinstance(f, DialogFilter) and f.title and getattr(f.title, 'text', str(f.title)).lower() == folder_name.lower():
                    # Keep the InputPeer objects themselves (they carry access_hash) rather
                    # than collapsing to a bare int id — a bare id that was never resolved
                    # via iter_dialogs()/get_entity() earlier in this session isn't
                    # resolvable on its own, so get_latest_vacancies() would fail with
                    # "Could not find the input entity" for every folder-sourced channel.
                    return list(f.include_peers)
        except Exception as e:
            logger.error(f"Error reading dialog filter (folder) '{folder_name}': {e}")
        return []

    async def get_source_channels(self, folder_name: str = "HR") -> list:
        """Gets target source channels, fallback to config env if folder query is empty."""
        # Check env variable first
        sources_str = os.environ.get("VACANCY_SOURCES", "")
        if sources_str:
            res = []
            for s in sources_str.split(","):
                s = s.strip()
                if not s:
                    continue
                if s.replace("-", "").isdigit():
                    res.append(int(s))
                else:
                    res.append(s)
            return res
            
        # Fallback to dialog filter
        channels = await self.get_channels_from_folder(folder_name)
        if channels:
            return channels
            
        # Automatic channel discovery if folder is empty or not found
        logger.info(f"Folder '{folder_name}' not found or empty. Scanning subscribed dialogs for vacancy channels...")
        auto_channels = []
        try:
            async for dialog in self.client.iter_dialogs(limit=100):
                if dialog.is_channel:
                    title = dialog.name.lower()
                    username = getattr(dialog.entity, 'username', '') or ''
                    username = username.lower()
                    keywords = ['job', 'vacancy', 'vakansiya', 'ish', 'work', 'toshkent', 'uzbekistan']
                    if any(kw in title or kw in username for kw in keywords):
                        # Avoid scraping our own target channel
                        target_channel = os.environ.get("VACANCY_TARGET_CHANNEL", "@nuvi_jobs").lower().replace("@", "")
                        if username != target_channel:
                            auto_channels.append(dialog.entity.id)
            logger.info(f"Auto-discovered {len(auto_channels)} vacancy source channels.")
        except Exception as e:
            logger.error(f"Error scanning dialogs for fallback: {e}")
        return auto_channels

    async def get_latest_vacancies(self, channels: list, limit: int = 5) -> list[dict]:
        """Reads latest messages from sources and filters for potential vacancies."""
        import pytz
        from datetime import datetime
        
        vacancies = []
        if not self.connected:
            return vacancies

        tz = pytz.timezone("Asia/Tashkent")
        now_tz = datetime.now(tz)

        for channel in channels:
            try:
                # `channel` is either a bare int id (auto-discovery path, already
                # resolvable because iter_dialogs() cached it earlier this session)
                # or an InputPeer object (folder path — usable as-is, no lookup needed).
                entity = channel if hasattr(channel, "SUBCLASS_OF_ID") else await self.client.get_entity(channel)
                async for msg in self.client.iter_messages(entity, limit=limit):
                    if msg.text and len(msg.text.strip()) > 30:
                        # 1. Date check: only vacancies posted TODAY (Tashkent calendar date)
                        msg_date_tz = msg.date.astimezone(tz)
                        if msg_date_tz.date() != now_tz.date():
                            continue
                            
                        text_lower = msg.text.lower()
                        # 2. General vacancy indicators
                        keywords = [
                            "vakansiya", "vacancy", "ishga taklif", "ishga", "ish bor",
                            "job", "lavozim", "talablar", "maosh", "oylik", "rezyume",
                            "kontakt", "aloqa", "kandidat", "salom"
                        ]
                        
                        # 3. IT-specific keywords (SMM, programmers, video editors, designers, QA, PMs, etc.)
                        it_keywords = [
                            "dasturchi", "developer", "programmer", "python", "javascript", "react", "flutter",
                            "node.js", "php", "golang", "devops", "backend", "frontend", "fullstack",
                            "smm", "marketing", "copywriter", "targetolog", "target", "dizayner", "designer",
                            "ux/ui", "motion", "montaj", "videomontaj", "video edit", "figma", "qa tester",
                            "testlovchi", "sysadmin", "tizim administrator", "project manager", "product manager"
                        ]
                        
                        if any(kw in text_lower for kw in keywords) and any(it_kw in text_lower for it_kw in it_keywords):
                            channel_id = getattr(msg.peer_id, 'channel_id', None)
                            if not channel_id:
                                channel_id = getattr(entity, 'id', None)

                            if channel_id and msg.id:
                                # entity may be a bare InputPeer (folder path) with no
                                # .title — the message's resolved .chat carries the
                                # actual Channel object with a real display name.
                                display_name = getattr(entity, 'title', None) or getattr(msg.chat, 'title', None) or f"channel {channel_id}"
                                vacancies.append({
                                    "channel_id": channel_id,
                                    "channel_name": display_name,
                                    "msg_id": msg.id,
                                    "text": msg.text,
                                    "date": msg.date
                                })
            except Exception as e:
                logger.warning(f"Failed to fetch vacancies from channel {channel}: {e}")
        return vacancies
