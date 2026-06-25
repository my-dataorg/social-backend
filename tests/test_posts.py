import uuid

VENUE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
OTHER_VENUE_ID = "11111111-2222-3333-4444-555555555555"


def test_list_venue_posts_empty(client):
    res = client.get(f"/v1/venues/{VENUE_ID}/posts")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["nextCursor"] is None
    assert data["totalApprox"] == 0


def test_create_and_list_venue_post(user_client):
    author = user_client("author-1")
    res = author.post(
        f"/v1/venues/{VENUE_ID}/posts",
        json={"body": "Great room tonight"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["body"] == "Great room tonight"
    assert data["venueId"] == VENUE_ID
    assert data["authorId"] == "author-1"
    assert data["id"]
    assert data["type"] == "text"
    assert "metadata" not in data or data["metadata"] is None

    reader = user_client("reader-2")
    listed = reader.get(f"/v1/venues/{VENUE_ID}/posts")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["body"] == "Great room tonight"
    assert items[0]["type"] == "text"


def test_checkin_post_includes_type_and_metadata(user_client, db, monkeypatch):
    from app.services.activity import process_checkin_created

    monkeypatch.setattr(
        "app.services.activity.user_has_subscription",
        lambda user_id, slug: slug == "social",
    )
    monkeypatch.setattr("app.services.activity.check_in_share_enabled", lambda user_id: True)

    process_checkin_created(
        db,
        {
            "checkInId": "cccccccc-dddd-eeee-ffff-000000000001",
            "venueId": VENUE_ID,
            "venueName": "Test Room",
            "userId": "author-1",
            "shareToSocial": True,
            "checkedInAt": "2026-06-23T20:00:00Z",
        },
    )

    reader = user_client("reader-2")
    listed = reader.get(f"/v1/venues/{VENUE_ID}/posts")
    item = listed.json()["items"][0]
    assert item["type"] == "checkin"
    assert item["metadata"] == {"checkinId": "cccccccc-dddd-eeee-ffff-000000000001"}


def test_venue_list_excludes_other_venues(user_client):
    author = user_client("author-1")
    author.post(f"/v1/venues/{VENUE_ID}/posts", json={"body": "Venue A"})
    author.post(f"/v1/venues/{OTHER_VENUE_ID}/posts", json={"body": "Venue B"})

    listed = author.get(f"/v1/venues/{VENUE_ID}/posts")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["body"] == "Venue A"


def test_create_post_without_venue(user_client):
    author = user_client("author-1")
    res = author.post("/v1/posts", json={"body": "General feed post"})
    assert res.status_code == 201
    data = res.json()
    assert data["venueId"] is None
    assert data["authorId"] == "author-1"

    listed = author.get(f"/v1/venues/{VENUE_ID}/posts")
    assert listed.json()["items"] == []


def test_create_post_with_optional_venue_id(user_client):
    author = user_client("author-1")
    res = author.post(
        "/v1/posts",
        json={"body": "Tagged via body", "venueId": VENUE_ID},
    )
    assert res.status_code == 201
    assert res.json()["venueId"] == VENUE_ID

    listed = author.get(f"/v1/venues/{VENUE_ID}/posts")
    assert len(listed.json()["items"]) == 1


def test_no_subscription_returns_403(no_subscription_client):
    res = no_subscription_client.get(f"/v1/venues/{VENUE_ID}/posts")
    assert res.status_code == 403

    res = no_subscription_client.post(
        f"/v1/venues/{VENUE_ID}/posts",
        json={"body": "Should fail"},
    )
    assert res.status_code == 403


def test_opaque_venue_id_no_validation(user_client):
    """Venue id is opaque — no FK check to pokerworld."""
    fake_venue = str(uuid.uuid4())
    author = user_client("author-1")
    res = author.post(
        f"/v1/venues/{fake_venue}/posts",
        json={"body": "Post at unknown venue"},
    )
    assert res.status_code == 201
    assert res.json()["venueId"] == fake_venue


def test_pagination_cursor(user_client, db):
    from app.models import Post
    from app.services.posts import create_post

    for i in range(3):
        create_post(db, author_id="author-1", body=f"Post {i}", venue_id=VENUE_ID)

    author = user_client("author-1")
    page1 = author.get(f"/v1/venues/{VENUE_ID}/posts", params={"limit": 2})
    assert page1.status_code == 200
    data1 = page1.json()
    assert len(data1["items"]) == 2
    assert data1["nextCursor"] == "2"
    assert data1["totalApprox"] == 3

    page2 = author.get(
        f"/v1/venues/{VENUE_ID}/posts",
        params={"limit": 2, "cursor": data1["nextCursor"]},
    )
    data2 = page2.json()
    assert len(data2["items"]) == 1
    assert data2["nextCursor"] is None
