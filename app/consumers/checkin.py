import json
import logging

from app.db import session as db_session
from app.events import get_nats
from app.services.activity import process_checkin_created

logger = logging.getLogger(__name__)

SUBJECT = "poker_world.checkin.created"
_subscription = None


async def _on_checkin_created(msg) -> None:
    try:
        envelope = json.loads(msg.data.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Invalid checkin.created payload: %s", exc)
        return

    if envelope.get("type") != SUBJECT:
        return

    data = envelope.get("data") or {}
    db = db_session.SessionLocal()
    try:
        process_checkin_created(db, data)
    except Exception as exc:
        logger.warning("Failed to process checkin.created: %s", exc)
        db.rollback()
    finally:
        db.close()


async def start_checkin_consumer():
    global _subscription
    nc = await get_nats()
    if not nc:
        return None
    _subscription = await nc.subscribe(SUBJECT, cb=_on_checkin_created)
    logger.info("Subscribed to %s", SUBJECT)
    return _subscription


async def stop_checkin_consumer() -> None:
    global _subscription
    if _subscription is None:
        return
    try:
        await _subscription.unsubscribe()
    except Exception as exc:
        logger.warning("Error unsubscribing from %s: %s", SUBJECT, exc)
    finally:
        _subscription = None
