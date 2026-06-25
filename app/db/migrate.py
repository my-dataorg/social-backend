from sqlalchemy import text
from sqlalchemy.engine import Engine


def run_migrations(engine: Engine) -> None:
    """Apply lightweight schema updates for local dev (no Alembic)."""
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id VARCHAR(36) PRIMARY KEY,
                    venue_id VARCHAR(36),
                    author_id VARCHAR(64) NOT NULL,
                    body VARCHAR(2000) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_posts_venue_created
                ON posts (venue_id, created_at DESC)
                """
            )
        )
        conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS post_type VARCHAR(32)"))
        conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS checkin_id VARCHAR(36)"))
        conn.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_checkin_id
                ON posts (checkin_id)
                WHERE checkin_id IS NOT NULL
                """
            )
        )
