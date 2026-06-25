import asyncio
import json
from sqlalchemy import select

from app.models import Post
from app.services.activity import CHECKIN_POST_TYPE, process_checkin_created

VENUE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CHECKIN_ID = "11111111-2222-3333-4444-555555555555"
USER_ID = "player-1"


def _event_data(**overrides):
    data = {
        "checkInId": CHECKIN_ID,
        "venueId": VENUE_ID,
        "venueName": "Bellagio Poker Room",
        "userId": USER_ID,
        "shareToSocial": True,
        "checkedInAt": "2026-06-23T20:00:00Z",
    }
    data.update(overrides)
    return data


def _allow_share(monkeypatch):
    monkeypatch.setattr(
        "app.services.activity.user_has_subscription",
        lambda user_id, slug: slug == "social",
    )
    monkeypatch.setattr("app.services.activity.check_in_share_enabled", lambda user_id: True)


def test_process_checkin_skips_when_not_sharing(db, monkeypatch):
    _allow_share(monkeypatch)
    result = process_checkin_created(db, _event_data(shareToSocial=False))
    assert result is None
    assert db.scalars(select(Post)).all() == []


def test_process_checkin_skips_without_social_subscription(db, monkeypatch):
    monkeypatch.setattr("app.services.activity.user_has_subscription", lambda *_: False)
    monkeypatch.setattr("app.services.activity.check_in_share_enabled", lambda _: True)
    result = process_checkin_created(db, _event_data())
    assert result is None


def test_process_checkin_skips_when_pref_disabled(db, monkeypatch):
    monkeypatch.setattr("app.services.activity.user_has_subscription", lambda *_: True)
    monkeypatch.setattr("app.services.activity.check_in_share_enabled", lambda _: False)
    result = process_checkin_created(db, _event_data())
    assert result is None


def test_process_checkin_creates_activity_post(db, monkeypatch):
    _allow_share(monkeypatch)
    result = process_checkin_created(db, _event_data())
    assert result is not None
    assert result.post_type == CHECKIN_POST_TYPE
    assert result.checkin_id == CHECKIN_ID
    assert result.venue_id == VENUE_ID
    assert result.author_id == USER_ID
    assert "Bellagio Poker Room" in result.body


def test_process_checkin_idempotent_on_checkin_id(db, monkeypatch):
    _allow_share(monkeypatch)
    first = process_checkin_created(db, _event_data())
    second = process_checkin_created(db, _event_data())
    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert len(db.scalars(select(Post)).all()) == 1


def test_process_checkin_missing_fields_noop(db, monkeypatch):
    _allow_share(monkeypatch)
    assert process_checkin_created(db, {"shareToSocial": True}) is None


def test_start_checkin_consumer_noops_without_nats(monkeypatch):
    from app.consumers import checkin as consumer_mod

    monkeypatch.setattr("app.events.settings.nats_url", "")
    sub = asyncio.run(consumer_mod.start_checkin_consumer())
    assert sub is None


def test_consumer_handles_envelope(db, monkeypatch):
    from app.consumers.checkin import _on_checkin_created

    _allow_share(monkeypatch)

    class FakeMsg:
        data = json.dumps(
            {
                "id": "evt_test",
                "type": "poker_world.checkin.created",
                "version": "1.0",
                "timestamp": "2026-06-23T20:00:00Z",
                "producer": "pokerworld-backend",
                "data": _event_data(),
            }
        ).encode()

    asyncio.run(_on_checkin_created(FakeMsg()))
    rows = db.scalars(select(Post).where(Post.checkin_id == CHECKIN_ID)).all()
    assert len(rows) == 1
    assert rows[0].post_type == CHECKIN_POST_TYPE


def test_consumer_ignores_invalid_json(db):
    from app.consumers.checkin import _on_checkin_created

    class FakeMsg:
        data = b"not-json"

    asyncio.run(_on_checkin_created(FakeMsg()))
    assert db.scalars(select(Post)).all() == []


def test_get_nats_noops_when_unset(monkeypatch):
    from app.events import get_nats

    monkeypatch.setattr("app.events.settings.nats_url", "")
    assert asyncio.run(get_nats()) is None


def test_platform_client_returns_false_without_token(monkeypatch):
    from app.clients.platform import user_has_subscription

    monkeypatch.setattr("app.clients.platform.settings.platform_internal_token", "")
    assert user_has_subscription("user-1", "social") is False


def test_poker_world_client_returns_false_without_token(monkeypatch):
    from app.clients.poker_world import check_in_share_enabled

    monkeypatch.setattr("app.clients.poker_world.settings.platform_internal_token", "")
    assert check_in_share_enabled("user-1") is False
