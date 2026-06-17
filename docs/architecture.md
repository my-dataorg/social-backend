# Architecture — social-backend (planned)

## Will own (PostgreSQL `social_db`)

- Posts, comments, reactions
- Typed relationships (parent, guardian, etc.)
- Follow graph

## Will not own

- User identity (JWT `sub` from Keycloak)
- Subscriptions (platform-backend)

## Education integration

Expose `GET /v1/users/{userId}/guardians` for education-backend to read guardian links — HTTP only, no shared DB.

## Auth

JWT + active `social` subscription (same pattern as education-backend).
