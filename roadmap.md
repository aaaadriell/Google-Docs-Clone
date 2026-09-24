# Real-Time Collaborative Docs — Build Roadmap

**Stack:** FastAPI (Python) backend + React/TypeScript frontend, Postgres (SQLAlchemy async), WebSockets for realtime, custom CRDT for conflict-free sync.

**MVP goal:** Users sign up, log in, create/open documents, share them by username, edit collaboratively in real time with autosave and minimal lag.

---

## Phase 0: Setup (2–3 days)

- [✅] Monorepo: `/frontend` (Vite + React + TS), `/backend` (FastAPI, `uv` or `poetry`)
- [ ] `docker-compose.yml` with Neon(Postgres)
- [ ] Alembic for migrations, SQLAlchemy async engine with `asyncpg`
- [ ] CI running lint + tests on both projects

**Done when:** `docker-compose up` gives a running Postgres, FastAPI on `/health`, and a blank Vite page.

---

## Phase 1: Auth — Signup, Login, Sessions (1 week)

**Backend**
- [ ] `User` table: id, username (unique), email, hashed_password, created_at
- [ ] `POST /auth/signup` — validate username uniqueness, hash password with `passlib` (bcrypt)
- [ ] `POST /auth/login` — verify password, issue JWT access token (+ refresh token, optional)
- [ ] `GET /auth/me` — returns current user from token
- [ ] `get_current_user` dependency used by all protected routes

**Frontend**
- [ ] Signup page (form, validation, error states)
- [ ] Login page (form, validation, error states)
- [ ] Store JWT — prefer httpOnly cookie over localStorage
- [ ] `useAuth` context/hook + protected-route wrapper redirecting to `/login`

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
