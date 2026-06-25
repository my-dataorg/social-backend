from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Post


def _parse_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return max(int(cursor), 0)
    except ValueError:
        return 0


def post_out(row: Post) -> dict:
    post_type = row.post_type or "text"
    metadata = None
    if post_type == "checkin" and row.checkin_id:
        metadata = {"checkinId": row.checkin_id}
    out = {
        "id": row.id,
        "venueId": row.venue_id,
        "authorId": row.author_id,
        "body": row.body,
        "type": post_type,
        "createdAt": row.created_at,
    }
    if metadata is not None:
        out["metadata"] = metadata
    return out


def create_post(
    db: Session,
    *,
    author_id: str,
    body: str,
    venue_id: str | None = None,
) -> Post:
    row = Post(author_id=author_id, body=body, venue_id=venue_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_venue_posts(
    db: Session,
    venue_id: str,
    *,
    cursor: str | None = None,
    limit: int = 24,
) -> dict:
    limit = min(max(limit, 1), 48)
    offset = _parse_cursor(cursor)

    total = db.scalar(
        select(func.count()).select_from(Post).where(Post.venue_id == venue_id)
    ) or 0

    rows = list(
        db.scalars(
            select(Post)
            .where(Post.venue_id == venue_id)
            .order_by(Post.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )

    next_offset = offset + limit
    next_cursor = str(next_offset) if next_offset < total else None
    return {
        "items": [post_out(row) for row in rows],
        "nextCursor": next_cursor,
        "totalApprox": total,
    }
