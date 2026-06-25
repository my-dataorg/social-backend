import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _internal_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Internal-Token": settings.platform_internal_token,
    }


def user_has_subscription(user_id: str, product_slug: str) -> bool:
    """Check subscription via platform internal API. Returns False if unavailable."""
    if not settings.platform_internal_token:
        logger.warning("PLATFORM_INTERNAL_TOKEN not set; skipping subscription check")
        return False

    url = (
        f"{settings.subscriptions_api_url.rstrip('/')}"
        f"/internal/users/{user_id}/subscriptions"
    )
    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(url, headers=_internal_headers())
            if res.status_code != 200:
                logger.warning(
                    "Platform subscription check failed for %s: %s",
                    user_id,
                    res.status_code,
                )
                return False
            slugs = {item["productSlug"] for item in res.json().get("items", [])}
            return product_slug in slugs
    except httpx.HTTPError as exc:
        logger.warning("Platform subscription check error for %s: %s", user_id, exc)
        return False
