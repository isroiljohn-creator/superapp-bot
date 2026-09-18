import logging
import time
from typing import Dict, Optional, Tuple

log = logging.getLogger("hirely.ratelimit")


class RateLimiter:
    """Fixed-window counter. Redis when configured (shared by all workers), in-process otherwise.
    Fails open: a limiter outage must never take the landing or the redirects down."""

    def __init__(self, redis_url: Optional[str]):
        self._redis = None
        self._local: Dict[str, Tuple[int, int]] = {}
        if redis_url:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(redis_url, socket_timeout=0.3, socket_connect_timeout=0.3)

    async def allow(self, key: str, limit: int, window: int) -> bool:
        if self._redis is not None:
            try:
                k = f"hl:rl:{key}:{int(time.time()) // window}"
                n = await self._redis.incr(k)
                if n == 1:
                    await self._redis.expire(k, window + 1)
                return n <= limit
            except Exception as exc:  # noqa: BLE001
                log.warning("redis rate limiter unavailable: %s", exc)
                return True
        bucket = int(time.time()) // window
        count, b = self._local.get(key, (0, bucket))
        count = count + 1 if b == bucket else 1
        self._local[key] = (count, bucket)
        if len(self._local) > 50000:
            self._local = {k: v for k, v in self._local.items() if v[1] == bucket}
        return count <= limit

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
