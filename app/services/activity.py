import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients import check_in_share_enabled, user_has_subscription
from app.models import Post

logger = logging.getLogger(__name__)

CHECKIN_POST_TYPE = "checkin"


def find_checkin_post(db: Session, checkin_id: str) -> Post | None:
    return db.scalar(select(Post).where(Post.checkin_id == checkin_id))


def create_checkin_activity(
    db: Session,
    *,
    checkin_id: str,
    venue_id: str,
    venue_name: str,
    user_id: str,
) -> Post:
    body = f"Checked in at {venue_name}" if venue_name else "Checked in at a poker venue"
    row = Post(
        author_id=user_id,
        body=body,
        venue_id=venue_id,
        post_type=CHECKIN_POST_TYPE,
        checkin_id=checkin_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def process_checkin_created(db: Session, data: dict) -> Post | None:
    """Create a feed post when check-in sharing is fully opted in."""
    if not data.get("shareToSocial"):
        return None

    user_id = data.get("userId")
    checkin_id = data.get("checkInId")
    venue_id = data.get("venueId")
    if not user_id or not checkin_id or not venue_id:
        logger.warning("checkin.created missing required fields: %s", data)
        return None

    existing = find_checkin_post(db, checkin_id)
    if existing:
        return existing

    if not user_has_subscription(user_id, "social"):
        return None
    if not check_in_share_enabled(user_id):
        return None

    return create_checkin_activity(
        db,
        checkin_id=checkin_id,
        venue_id=venue_id,
        venue_name=data.get("venueName") or "",
        user_id=user_id,
    )
