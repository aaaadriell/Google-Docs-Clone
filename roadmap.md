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

**Backend — How the two tokens fit together (read before Steps 3–4)**
> Your backend accepts **two different credentials**, and every endpoint uses exactly one of them:
>
> | Credential | Sent how | Proves | Used by |
> |---|---|---|---|
> | **Access token (JWT)** | `Authorization: Bearer <jwt>` header — the frontend adds it | "I am user X, right now" (for 15 min) | **Every** protected API: `/me`, `/documents`, … |
> | **Refresh token** | httpOnly cookie — the browser adds it automatically | "I have a live session" (for 7 days) | **Only** `/refresh` and `/logout` |
>
> - The "middleware" for protected APIs is a FastAPI **dependency** called `get_current_user`. You add it as a parameter to an endpoint; FastAPI runs it **before** the endpoint body. It reads the Bearer header, verifies the JWT, loads the user, and either hands the endpoint a `User` or stops the request with a **401**. The endpoint itself never touches tokens.
> - `/refresh` is **not** protected by `get_current_user` — it's called precisely *because* the access token is missing or expired. It authenticates with the **cookie** instead.
> - `/refresh` is therefore more than `create_jwt_token`: it is "**verify the refresh cookie** (signature, expiry, DB row, `isActive`), and only then call `create_jwt_token`." Skipping the checks would hand a fresh access token to anyone with an old or logged-out cookie.
>
> Full flow on the home page:
> ```
> page load ─► POST /refresh (cookie) ─► 200 {jwtToken, user} ─► store in AuthContext
>                                    └─► 401 ─► /login
> GET /me  (Bearer jwt) ─► get_current_user ─► OK ─► endpoint returns the user
>                                          └─► 401 "expired" ─► frontend calls /refresh, retries once
>                                          └─► 401 "invalid" ─► frontend logs out
> ```

**Backend — Step 3: Access-token auth (`get_current_user`) + `GET /me`**
> Build this first: it's the gate every future API (documents, sharing, …) goes through, and `/me` is the simplest endpoint to prove it works.

*3a. Fix the access-token helpers (`jwtTokenHelpers.py`)*
- [✅] Add the fail-fast check: `if not SECRET_KEY: raise RuntimeError(...)` at module level (same as `refreshTokenHelpers.py`)
  - Why: a missing `JWT_SECRET_KEY` should stop the app at startup, not break the first login
- [✅] In `decode_jwt_token`, put `except jwt.ExpiredSignatureError` **before** `except jwt.InvalidTokenError`
  - Why: `ExpiredSignatureError` is a *subclass* of `InvalidTokenError`; Python uses the **first** matching `except`, so in the current order the "expired" branch never runs and every expired token is reported as invalid
  - Why it matters: "expired" means *refresh and retry*; "invalid" means *log out*. The frontend can only make that choice if the backend tells them apart

*3b. The dependency — new file `app/dependencies.py`*
- [✅] `bearer_scheme = HTTPBearer(auto_error=False)`
  - What: FastAPI's helper that reads the `Authorization: Bearer <token>` header and gives you the token string (`credentials.credentials`)
  - Why `auto_error=False`: by default it rejects missing headers itself with its own status/message; turning that off lets **you** return a consistent 401 for every failure
  - Bonus: it adds an **Authorize** button to `/docs`, so you can paste a token and test protected endpoints there
- [✅] `def get_current_user(db: db_session, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]) -> User`
  - What: the reusable "gate". It's a normal function, but because endpoints list it via `Depends`, FastAPI runs it before them — that's the "middleware" behaviour
  - It's a **dependency**, not a helper, so it uses `db: db_session` (FastAPI injects it). Helpers use `db: Session`
- [ ] Inside `get_current_user`, in order:
  - [✅] No credentials → `raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})`
  - [ ] `decode_jwt_token(credentials.credentials)`:
    - `ExpiredJWTTokenError` → 401 with detail `"Access token expired"` → frontend's signal to call `/refresh`
    - `InvalidJWTTokenError` → 401 with detail `"Invalid access token"` → frontend's signal to log out
  - [ ] `user = db.get(User, payload["user_id"])`; `None` → 401 (user deleted after the token was issued)
  - [ ] Return `user`
  - Why `raise` is fine here (unlike `/refresh`): there's no cookie to clear, so nothing is lost when FastAPI discards the response
  - Why `WWW-Authenticate: Bearer`: the HTTP standard says a 401 should tell the client which auth scheme to use
- [ ] `CurrentUser = Annotated[User, Depends(get_current_user)]` — same idea as your `db_session` alias, so endpoints just write `current_user: CurrentUser`

*3c. `GET /me` — first protected endpoint*
- [ ] Schema `UserPublic` in `schemas.py`: `id`, `username`, `email`, `created_at` (`from_attributes = True`) — the safe, public view of a user (never `hashed_password`). Reuse it in `/refresh` and later `/login`
- [ ] `@app.get("/me", response_model=UserPublic)` → `def me(current_user: CurrentUser): return current_user`
  - Why it's one line: the dependency already did all the work — this is the pattern every protected endpoint will follow
  - Why it exists: the home page needs "who am I?", and it's the simplest end-to-end test of the whole chain

*3d. Testing*
- [ ] Postman: log in → copy `jwtToken` → **Authorization** tab → *Bearer Token* → `GET /me` → **200** with your user
- [ ] No header → **401** "Not authenticated"
- [ ] Change one character of the token → **401** "Invalid access token"
- [ ] Send the **refresh** token as the Bearer token → **401** "Invalid access token"
- [ ] Temporarily set `ACCESS_TOKEN_EXPIRE_MINUTES = 1` → wait → **401** "Access token expired" (then set it back to 15)
- [ ] `/docs` → **Authorize** → paste token → try `/me` there too

**Backend — Step 4: `POST /refresh` (v1 — no rotation)**
> Purpose: the frontend calls this on **every page load / reload** (the in-memory access token is always gone) and whenever an API call returns **401 "Access token expired"**. It authenticates with the **refresh cookie**, not the Bearer header. Valid → issue a **new access token only**; the refresh token and cookie stay unchanged. Invalid for any reason → 401 + clear cookie, and the frontend sends the user to `/login`. An invalid refresh token is **never** exchanged for anything.

*4a. Prerequisites*
- [ ] Schema `RefreshResponse`: `jwtToken: str` + `user: UserPublic`
  - Why both: after a reload the frontend has lost the token **and** who the user is; returning the user here saves an extra `/me` call
- [ ] Helper `unauthorized_and_clear_cookie() -> JSONResponse` in `refreshTokenHelpers.py`: builds a 401 `JSONResponse` with one fixed, vague detail (`"Invalid or expired session."`), calls `clear_refresh_cookie` on it, returns it
  - Why **return** instead of `raise HTTPException`: raising **discards** the injected response, so the cookie deletion would be lost (the bug you saw in `/logout`)
  - Why clear the cookie: so the browser stops sending a token that can never work
  - Why one vague message: don't reveal to a caller *which* check failed

*4b. Endpoint signature*
- [ ] `@app.post("/refresh", response_model=RefreshResponse)`
- [ ] Params: `db: db_session`, `refresh_token: Annotated[str | None, Cookie()] = None`
  - **No** `CurrentUser` — the access token is missing/expired when this is called; the cookie is the credential
  - No `response: Response` needed — the success path doesn't touch the cookie in v1

*4c. Checks — in this order, stop at the first failure*
- [ ] **No cookie** (`refresh_token is None`) → return a plain 401 (nothing to clear)
  - Happens when: never logged in, already logged out, or the browser dropped the expired cookie
- [ ] **Decode fails** (`decode_refresh_token` raises `InvalidRefreshTokenError`) → `return unauthorized_and_clear_cookie()`
  - Happens when: **expired** (PyJWT checks `exp` — this is the "refresh token expiry has passed" case), tampered, garbage, or an access token was sent
  - No need to set `isActive=False` — an expired token is already unusable; cleanup (Step 5) deletes its row later
- [ ] **Row not found** (`get_refresh_token_from_db(db, payload["jti"])` returns `None`) → `return unauthorized_and_clear_cookie()`
  - Happens when: the token is genuine but its row was deleted (cleanup / manual)
- [ ] **Row inactive** (`record.isActive is False`) → `return unauthorized_and_clear_cookie()`
  - Happens when: this session was logged out (possibly via another copy of the cookie), or revoked
  - **This check is what makes logout real** — without it, a copied cookie keeps minting access tokens until it expires
- [ ] **User missing** (`db.get(User, payload["user_id"])` is `None`) → `return unauthorized_and_clear_cookie()`
  - Defensive: user deleted mid-session — don't crash with a 500

*4d. Success path*
- [ ] `create_jwt_token(user.id)` → new access token — **this** is the part that's "just `create_jwt_token`"; everything above is what makes it safe to call
- [ ] Return `RefreshResponse(jwtToken=..., user=user)`
- [ ] No DB writes, no commit, no cookie changes
- [ ] Wrap the DB lookups in `try/except Exception` → log + 500 (unexpected errors only; the auth failures above are returns, not exceptions)

*4e. Testing (Postman + Neon)*
- [ ] Log in → `/refresh` → **200**, body has `jwtToken` + `user`, cookie value **unchanged**
- [ ] Use that new `jwtToken` on `GET /me` → **200** (proves Step 3 + Step 4 work together)
- [ ] Call `/refresh` several times → each returns a different `jwtToken`; cookie unchanged; no new rows in Neon
- [ ] No cookie → **401**
- [ ] Cookie = `garbage` → **401**, cookie cleared
- [ ] Log out → `/refresh` → **401**
- [ ] **Copied cookie:** log in, copy the cookie value, log out, set the copied value back, `/refresh` → **401** (proves the `isActive` check)
- [ ] Set the row's `isActive=false` by hand in Neon → `/refresh` → **401**
- [ ] Access token sent as the refresh cookie → **401**
- [ ] **Full expiry loop:** `ACCESS_TOKEN_EXPIRE_MINUTES = 1` → log in → wait → `/me` → 401 "expired" → `/refresh` → new token → `/me` → **200**

**Later — Step 4 v2: Rotation + reuse detection (not needed for MVP)**
> Upgrade path once everything else works. Same endpoint, same response shape — only the success branch and the inactive-row branch change; the frontend needs no changes.
- [ ] Add `revoked_at` column (timestamp of deactivation)
- [ ] Success path: deactivate old row (`isActive=False`, `revoked_at=now`) + `create_refresh_token` + set new cookie, **one** commit → sliding sessions (active users stay logged in)
- [ ] Inactive row with `revoked_at` older than ~10–30 s → **reuse detected**: deactivate all of that user's rows
- [ ] Inactive row with `revoked_at` within ~10–30 s → multi-tab race, not theft: plain 401, don't clear cookie, don't mass-revoke
- [ ] Tradeoff being bought: stolen refresh tokens get detected, and daily users are no longer logged out every `REFRESH_TOKEN_EXPIRE_DAYS`

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
- [ ] `apiFetch` wrapper: adds `Authorization: Bearer`; on 401 `"Access token expired"` → `/refresh` once → retry once; on any other 401 (or a failed refresh) → force logout; concurrent 401s share **one** refresh call
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
