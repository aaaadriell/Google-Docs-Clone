# Real-Time Collaborative Docs — Build Roadmap

**Stack:** FastAPI (Python) backend + React/TypeScript frontend, Postgres (SQLAlchemy async), WebSockets for realtime, custom CRDT for conflict-free sync.

**MVP goal:** Users sign up, log in, create/open documents, share them by username, edit collaboratively in real time with autosave and minimal lag.

---

## Phase 0: Setup (2–3 days)

- [✅] Monorepo: `/frontend` (Vite + React + TS), `/backend` (FastAPI, `uv` or `poetry`)
- [✅] `docker-compose.yml` with Neon(Postgres)
- [✅] Alembic for migrations, SQLAlchemy async engine with `asyncpg`
- [ ] CI running lint + tests on both projects

**Done when:** `docker-compose up` gives a running Postgres, FastAPI on `/health`, and a blank Vite page.

---

## Phase 1: Auth — Signup, Login, Sessions (1 week)

**Backend — Users**
- [✅] `User` table: id, username (unique), email, hashed_password, created_at
- [✅] `POST /signup` — validate username uniqueness, hash password with `bcrypt`
- [✅] `POST /login` — verify password, issue JWT access token

**Backend — Session model (rules to follow throughout)**
> - Every login creates a **new** refresh token + DB row (one row = one device/session). Never reuse an existing one.
> - The JWT payload only carries identity + `jti`; session state (`isActive`) lives **only** in the DB row.
> - The refresh token is **fixed for the life of the session** (no rotation in v1): `/refresh` only issues new access tokens. Sessions last exactly `REFRESH_TOKEN_EXPIRE_DAYS` from login.
> - A refresh token is only honoured if it is genuine **and** unexpired **and** its row exists **and** `isActive=True` — expiry alone is never enough (logout / revocation must take effect).

**Backend — Step 1: Token helpers**
- [✅] `refresh_tokens` table: id, jti (unique), user_id (FK → users, cascade), created_at, expired_at, isActive (+ migration)
- [✅] `create_refresh_token(db, user_id)` — adds row (no commit), returns token
- [✅] Remove `"isActive"` claim from the refresh token payload (DB is the source of truth)
- [✅] Fail fast at startup if `JWT_SECRET_KEY` / `REFRESH_SECRET_KEY` is missing
- [✅] Custom `InvalidRefreshTokenError` exception
- [✅] `decode_refresh_token(token)` — `algorithms=[...]`, `options={"require": ["exp","iat","jti","user_id"]}`, checks refresh flag, single `except jwt.InvalidTokenError as e: raise InvalidRefreshTokenError from e`; no DB, no HTTPException
- [✅] `decode_access_token(token)` — same pattern for access tokens (distinguish expired vs invalid)
- [✅] `get_refresh_token_from_db(db, jti)` — look up row by jti
- [✅] `set_refresh_cookie(response, token)` / `clear_refresh_cookie(response)` — one shared set of settings (key, path, httponly, secure, samesite, max_age from `REFRESH_TOKEN_EXPIRE_DAYS`)
- [✅] Use `set_refresh_cookie` in `/login` (replace the inline `set_cookie`)

**Backend — Step 2: `POST /logout`**
- [✅] Route decorator, read cookie via `Cookie()` param (not `response.cookies`)
- [✅] Decode → find row by jti → `isActive=False` → commit
- [✅] Always `clear_refresh_cookie`, always return 204 (missing/invalid/already-revoked cookie is not an error)

**Backend — Step 3: `POST /refresh` (v1 — no rotation)**
> Purpose: the frontend calls this on **every page load / reload** (the in-memory access token is always gone) and whenever an API call returns **401** (access token expired). The server — not the frontend, which can't read the httpOnly cookie — checks the refresh token. If Valid → issue a **new access token only**; the refresh token and cookie stay unchanged. Invalid for any reason → 401 + clear cookie, and the frontend sends the user to `/login`. An invalid refresh token is **never** exchanged for anything.

*3a. Prerequisites*
- [ ] Response schema `UserPublic` in `schemas.py`: `id`, `username`, `email` (reuse it in `/login` and `/me` too)
- [ ] Response schema `RefreshResponse`: `jwtToken: str` + `user: UserPublic` — the frontend loses both the token and the user on reload, so it needs both back
- [ ] Helper `unauthorized_and_clear_cookie() -> JSONResponse` in `refreshTokenHelpers.py`: builds a 401 `JSONResponse` with one fixed, vague detail (`"Invalid or expired session."`), calls `clear_refresh_cookie` on it, returns it
  - Why: `raise HTTPException` **discards** the injected `response`, so the cookie deletion would be lost — failure paths must **return** this response instead of raising
  - Why one vague message: don't reveal to a caller *which* check failed

*3b. Endpoint signature*
- [ ] `@app.post("/refresh", response_model=RefreshResponse)`
- [ ] Params: `db: db_session`, `refresh_token: Annotated[str | None, Cookie()] = None`
  - No `response: Response` needed — the success path doesn't touch the cookie in v1

*3c. Checks — in this order, stop at the first failure*
- [ ] **No cookie** (`refresh_token is None`) → return a plain 401 (nothing to clear)
  - Happens when: never logged in, already logged out, or the browser dropped the expired cookie
- [ ] **Decode fails** (`decode_refresh_token` raises `InvalidRefreshTokenError`) → `return unauthorized_and_clear_cookie()`
  - Happens when: **expired** (PyJWT checks `exp` for you — this is the "expiry date has passed" case), tampered, garbage, or an access token was sent
  - No need to set `isActive=False` here — an expired token is already unusable; cleanup (Step 5) deletes its row later
- [ ] **Row not found** (`get_refresh_token_from_db(db, payload["jti"])` returns `None`) → `return unauthorized_and_clear_cookie()`
  - Happens when: the token is genuine but its row was deleted (cleanup / manual)
- [ ] **Row inactive** (`record.isActive is False`) → `return unauthorized_and_clear_cookie()`
  - Happens when: this session was logged out (possibly from another copy of the cookie), or revoked
  - **This check is what makes logout real** — without it, a copied cookie keeps minting access tokens until it expires
- [ ] **User missing** (`db.get(User, payload["user_id"])` is `None`) → `return unauthorized_and_clear_cookie()`
  - Defensive: user deleted mid-session — don't crash with a 500

*3d. Success path*
- [ ] `create_jwt_token(user.id)` → new access token
- [ ] Return `RefreshResponse(jwtToken=..., user=UserPublic(...))`
- [ ] No DB writes, no commit, no cookie changes
- [ ] Wrap the DB lookups in `try/except Exception` → log + 500 (unexpected errors only; the auth failures above are returns, not exceptions)

*3e. Testing (Postman + Neon)*
- [ ] Log in → `/refresh` → **200**, body has `jwtToken` + `user`, cookie value **unchanged**
- [ ] Call `/refresh` several times → each returns a new, different `jwtToken`; refresh cookie still unchanged; no new rows in Neon
- [ ] Decode the new `jwtToken` on jwt.io → `user_id` matches, `exp` ≈ now + 15 min
- [ ] No cookie → **401**
- [ ] Cookie = `garbage` → **401**, cookie cleared
- [ ] Log out → `/refresh` → **401**
- [ ] **Copied cookie:** log in, copy the cookie value, log out, manually set the copied value back, `/refresh` → **401** (proves the `isActive` check works)
- [ ] Set the row's `isActive=false` by hand in Neon → `/refresh` → **401**
- [ ] Access token sent as the refresh cookie → **401**
- [ ] (Optional) Temporarily set `REFRESH_TOKEN_EXPIRE_DAYS` to a tiny value (e.g. via minutes) → wait → `/refresh` → **401**

**Later — Step 3 v2: Rotation + reuse detection (not needed for MVP)**
> Upgrade path once everything else works. Same endpoint, same response shape — only the success branch and the inactive-row branch change; the frontend needs no changes.
- [ ] Add `revoked_at` column (timestamp of deactivation)
- [ ] Success path: deactivate old row (`isActive=False`, `revoked_at=now`) + `create_refresh_token` + set new cookie, **one** commit → sliding sessions (active users stay logged in)
- [ ] Inactive row with `revoked_at` older than ~10–30 s → **reuse detected**: deactivate all of that user's rows
- [ ] Inactive row with `revoked_at` within ~10–30 s → multi-tab race, not theft: plain 401, don't clear cookie, don't mass-revoke
- [ ] Tradeoff being bought: stolen refresh tokens get detected, and daily users are no longer logged out every `REFRESH_TOKEN_EXPIRE_DAYS`

**Backend — Step 4: Protecting routes**
- [ ] `get_current_user` dependency (`HTTPBearer` → `decode_access_token` → load user) → 401 + `WWW-Authenticate: Bearer` on failure
- [ ] `CurrentUser = Annotated[User, Depends(get_current_user)]` alias
- [ ] `GET /me` — returns current user (end-to-end test of the chain)

**Backend — Step 5: Cleanup**
- [ ] `delete_stale_refresh_tokens(db)` — delete rows where `expired_at < now` OR (`isActive=False` AND older than N days)
- [ ] Call it at login (move to a scheduled job later)

**Frontend**
- [✅] Signup page (form, validation, error states)
- [✅] Login page (form, validation, error states, `credentials: 'include'`)
- [✅] Store JWT — in memory (`AuthContext`)
- [✅] Store Refresh Token — HttpOnly cookie (set by backend)
- [✅] `useAuth` context/hook
- [ ] `AuthContext.status`: `"loading" | "authenticated" | "unauthenticated"`
- [ ] On app start: silent `POST /refresh` (`credentials: 'include'`) → success stores JWT + user, failure → unauthenticated
- [ ] `ProtectedRoute`: loading → spinner, unauthenticated → `<Navigate to="/login" replace />`, authenticated → page
- [ ] `logout()`: async — `POST /logout` with `credentials: 'include'`, clear JWT + user in `finally`, then redirect
- [ ] `apiFetch` wrapper: adds `Authorization: Bearer`, on 401 → refresh once → retry once → else force logout; concurrent 401s share **one** refresh call
- [ ] HomePage calls `GET /me` through `apiFetch`; remove the on-screen JWT debug line

**Done when:** you can sign up, log in, land on an (empty) home page, and a protected route returns 401 without a valid token.

---

## Phase 2: Home Page — Create and Open Docs (1 week)

**Backend**
- [ ] `Document` table: id, title, owner_id, content (text), created_at, updated_at
- [ ] `POST /documents` — create a doc owned by current user
- [ ] `GET /documents` — list docs owned by or shared with current user
- [ ] `GET /documents/{id}` — fetch one doc's content, with access check

**Frontend**
- [ ] Home page: doc list (title + last updated), "New Document" button, click to open
- [ ] Doc editor page (plain `<textarea>` for now), loads content via `GET /documents/{id}`

**Done when:** logged in, you see your docs on a home page, can create a new one, and reopen an old one with content intact.

---

## Phase 3: Autosave and Persistence (3–4 days)

- [ ] Debounce edits (~500ms after last keystroke), `PATCH /documents/{id}`
- [ ] "Saving… / Saved" indicator in the UI
- [ ] Handle tab-close mid-edit: `beforeunload` + `navigator.sendBeacon` for a final save
- [ ] Backend updates `updated_at` on every save (for sorting on home page)

**Done when:** you type, close the tab immediately, reopen the doc, and your last changes are there.

---

## Phase 4: Sharing by Username (1 week)

- [ ] `DocumentPermission` table: doc_id, user_id, role (owner/editor)
- [ ] `POST /documents/{id}/share` — body `{ username: str }`, 404 if username doesn't exist, else insert permission row
- [ ] `GET /documents/{id}/collaborators` — list who has access
- [ ] Update `GET /documents` to include docs shared with you (visually distinct, e.g. "Shared by X")
- [ ] Enforce permission checks on every document route (403 for no access)

**Done when:** User A shares a doc with User B by username; User B sees it on their home page and can open/edit it.

---

## Phase 5: Real-Time Sync — Naive → Op-Based → CRDT (2–3 weeks)

This is the core technical phase. Build it in three deliberate steps so you understand *why* each one is needed.

### 5a. WebSocket relay (few days)
- [ ] `@app.websocket("/ws/documents/{doc_id}")`, authenticated via JWT (query param or initial message)
- [ ] In-memory `dict[doc_id, set[WebSocket]]` room registry
- [ ] Broadcast full document content naively on every change
- [ ] Open two tabs, type in both — observe data loss (expected, document what breaks)

### 5b. Operation-based messages (few days)
- [ ] Define `Op` types in TypeScript: `insert (pos, char)` / `delete (pos)`
- [ ] Backend relays ops and appends to `operations` table (doc_id, op JSONB, client_id, seq, created_at)
- [ ] Reproduce and document a concurrent-edit divergence bug (e.g. insert vs. delete shifting positions)

### 5c. Custom CRDT (the core 1–2 weeks)
- [ ] Implement a sequence CRDT (RGA) **entirely in TypeScript**, client-side
  - Unique ID per character: `{ siteId, counter }`
  - Inserts reference the preceding character's ID (not a numeric index)
  - Deletes become tombstones
- [ ] Keep Python backend as a dumb relay + append-only op log (no CRDT semantics needed server-side)
- [ ] Property-based tests with `fast-check`: simulate multiple clients, apply random concurrent op sequences in different orders, assert convergence
- [ ] Wire the CRDT into your real editor, replacing the naive broadcast from 5a

**Done when:** two logged-in users with edit access see each other's keystrokes within tens of milliseconds, and randomized convergence tests pass reliably.

---

## Phase 6: Low-Lag Polish (1 week)

- [ ] Apply local edits optimistically (update own screen instantly, don't wait on round trip)
- [ ] Batch rapid keystrokes into fewer WebSocket messages (e.g. flush every 20–30ms) instead of one per character
- [ ] Lightweight presence: colored dot/name per connected user
- [ ] (Optional) live cursor positions anchored to CRDT character IDs
- [ ] Measure and log round-trip latency (timestamp echo) for real p50/p95 numbers

**Done when:** typing feels instant locally, and you can quote a real p50/p95 latency number for edits reaching other clients.

---

## Phase 7: Robustness (1 week)

- [ ] Reconnect logic: buffer local ops on disconnect, request "ops since my last known seq" on reconnect, replay
- [ ] Periodic CRDT state snapshotting so new/reconnecting clients don't replay full history
- [ ] Handle "access revoked mid-session" gracefully

**Done when:** you can kill your network mid-edit, edit offline, reconnect, and merge cleanly with no data loss.

---

## Phase 8: Showcase (a few days)

- [ ] README with architecture diagram (auth flow, REST for CRUD, WebSocket + CRDT for realtime, Postgres as source of truth)
- [ ] Demo GIF: two browser windows editing live, one user sharing a doc with another by username
- [ ] Short write-up: why the CRDT lives client-side only, what broke in the naive/op-based phases, your latency numbers

---

## Stack-Specific Gotchas to Remember

- **asyncio + blocking calls:** avoid synchronous DB calls inside `async def` routes — they block the whole event loop for that worker. Use `asyncpg` throughout.
- **WebSocket + Pydantic:** validate incoming WebSocket messages with Pydantic models, same as REST bodies.
- **Type-sharing:** Python and TypeScript don't share types automatically — consider generating TS types from Pydantic models, or hand-sync a small shared schema for your `Op` format.
- **Multi-worker scaling (future):** in-memory room registries don't broadcast across separate Uvicorn workers — you'd need Redis pub/sub if you scale beyond a single process.
