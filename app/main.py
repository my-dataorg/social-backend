from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth import require_social_subscription
from app.config import settings
from app.consumers.checkin import start_checkin_consumer, stop_checkin_consumer
from app.db.migrate import run_migrations
from app.db.session import engine, get_db
from app.events import close_nats
from app.models import Base
from app.schemas import PostCreate, PostOut, PostPage
from app.services.posts import create_post, list_venue_posts, post_out

User = dict


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    await start_checkin_consumer()
    yield
    await stop_checkin_consumer()
    await close_nats()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/me")
def me(user: User = Depends(require_social_subscription)):
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


@app.post("/v1/posts", response_model=PostOut, status_code=201)
def create_post_route(
    body: PostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_social_subscription),
):
    row = create_post(
        db,
        author_id=user["id"],
        body=body.body,
        venue_id=body.venueId,
    )
    return PostOut(**post_out(row))


@app.get("/v1/venues/{venue_id}/posts", response_model=PostPage)
def list_venue_posts_route(
    venue_id: str,
    cursor: str | None = None,
    limit: int = Query(default=24, ge=1, le=48),
    db: Session = Depends(get_db),
    _: User = Depends(require_social_subscription),
):
    page = list_venue_posts(db, venue_id, cursor=cursor, limit=limit)
    return PostPage(**page)


@app.post("/v1/venues/{venue_id}/posts", response_model=PostOut, status_code=201)
def create_venue_post_route(
    venue_id: str,
    body: PostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_social_subscription),
):
    row = create_post(
        db,
        author_id=user["id"],
        body=body.body,
        venue_id=venue_id,
    )
    return PostOut(**post_out(row))
