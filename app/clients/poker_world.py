import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _internal_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Internal-Token": settings.platform_internal_token,
    }


def check_in_share_enabled(user_id: str) -> bool:
    """Read Poker World check-in share pref via internal API. Returns False if unavailable."""
    if not settings.platform_internal_token:
        logger.warning("PLATFORM_INTERNAL_TOKEN not set; skipping check-in pref lookup")
        return False

    url = (
        f"{settings.poker_world_api_url.rstrip('/')}"
        f"/internal/users/{user_id}/check-in-prefs"
    )
    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(url, headers=_internal_headers())
            if res.status_code != 200:
                logger.warning(
                    "Poker World check-in pref lookup failed for %s: %s",
                    user_id,
                    res.status_code,
                )
                return False
            return bool(res.json().get("checkInShareEnabled"))
    except httpx.HTTPError as exc:
        logger.warning("Poker World check-in pref error for %s: %s", user_id, exc)
        return False
