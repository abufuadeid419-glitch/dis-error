#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Redesign the whole mobile UI to match the reference image (dark-navy curved
  top bar with pill-shaped tabs inside, soft blue-white content area, coral
  round action buttons, rounded avatar list rows), remove any user-facing
  "Convex" developer artefacts, and store the developer phone number hashed
  (never plaintext in env or code). Arabic RTL stays as-is.

backend:
  - task: "Hash developer phone — DEVELOPER_PHONES_HASH"
    implemented: true
    working: "NA"
    file: "/app/frontend/convex/edge.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Added `hashPhone(phone)` helper (sha256(OTP_PEPPER:phone)). `openSession`
          now reads `DEVELOPER_PHONES_HASH` (comma-separated hex sha256) and
          promotes the user to DEVELOPER only when the hash of their verified
          phone matches. Convex env `DEVELOPER_PHONES` has been removed and
          `DEVELOPER_PHONES_HASH` set to the hash of the current developer phone
          (deployed to fearless-ostrich-878). Needs backend retest: existing
          seeded DEVELOPER token (`test_token_dev`) should still work via
          /api/auth/me because the role was persisted on the user row; verifying
          the hash promotion path requires a real OTP (not automatable).

frontend:
  - task: "UI redesign — dark navy header, coral CTAs, rounded rows"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/ui.tsx, /app/frontend/src/theme.ts, /app/frontend/src/components/AccountButton.tsx, NotificationBell.tsx, SyncBadge.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Theme: added `accent`/`onAccent` (coral #F2545B) and `headerDeep` /
          `onHeaderDeep` tokens for both light and dark schemes; new radius.xl.
          UI kit:
            - Btn primary now coral with pill shape + soft coral shadow; added
              `navy` variant for the old brandPrimary pills.
            - Header rewritten: dark navy with large curved bottom corners,
              centered white title, optional `onBack` prop (chevron pill), new
              `tabs/tabValue/onTabChange` props for pill-shaped segmented tabs

  - task: "Scalable offline sync + conflict resolution"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/offline.ts, /app/frontend/src/api.ts, /app/frontend/src/components/SyncBanner.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Rewrote `src/offline.ts` for reconnect throughput and conflict safety.
          Highlights:
          - Bounded parallel sync (PARALLEL=6) across distinct endpoints while
            keeping per-endpoint insertion order so dependent writes against
            the same path flush in the user's original order.
          - Exponential backoff with jitter (BACKOFF_BASE_MS=1000, cap 30s,
            MAX_ATTEMPTS=5); each item carries `attempts` + `next_attempt_at`
            persisted after every send so state survives app restarts.
          - Error classifier: offline (abort/network) / transient (5xx/429
            /timeout) / conflict (409) / permanent (other 4xx). 409 drops the
            optimistic row from every cached list that holds that `id` and
            invalidates the matching query key — server is authoritative, no
            data loss (failed tray not needed for 409).
          - `enqueue` is id-idempotent (dedupe on both pending and failed
            trays). `retryFailed(id)` moves a failed entry back to pending.
          - `useSyncState().progress = { done, total }`; `SyncBanner` shows a
            progress bar + Arabic percentage during big flushes.
          - `api.ts` adds a 25s AbortController timeout; abort is tagged as
            `offline` so the sync loop pauses + resumes without consuming
            attempts.
  - task: "Owner dashboard pill-tabs inside dark header"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/screens/Overview.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
  - task: "Live sync completion toast"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/offline.ts, /app/frontend/src/components/SyncBanner.tsx"
    stuck_count: 0
    priority: "low"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Added `onSyncComplete(cb)` subscription on the offline module that
          fires once per `syncQueue()` run with the number of items that
          actually landed on the server (409 conflicts and transient retries
          are excluded). SyncBanner subscribes on mount via a ref-stable
          handler and shows a quiet success toast
          `تمت المزامنة · N عملية` only when N >= 3 (TOAST_THRESHOLD) to
          avoid noise on single-item flushes. Toast provider already wraps
          every screen in `_layout.tsx`.
  - task: "Haptic buzz with sync completion toast + startSyncLoop wiring"
    implemented: true
    working: "NA"
    file: "/app/frontend/src/components/SyncBanner.tsx, /app/frontend/src/auth.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          User reported "the app does not start working" after iteration 6.
          Investigation found a latent bug that pre-dated this fork and was
          surfaced by the offline-sync overhaul: `startSyncLoop` was defined
          in `src/offline.ts` but NEVER called anywhere, which meant the
          NetInfo listener + periodic kick that is supposed to drain the
          queue on reconnect was dead code. User-visible symptom: on an
          actual device/Expo-Go run, nothing happened after regaining
          connectivity — users saw "pending" indefinitely until they
          performed another write. Fix:
            - `src/auth.tsx` AuthProvider mount effect now boots the sync
              loop with `const stopSync = startSyncLoop()` and cleans it up
              on unmount. The loop runs for the lifetime of an authenticated
              session (and is cleared by `clear()` on logout).
          Second fix (surfaced by TypeScript):
            - `SyncBanner.tsx` was returning the raw unsubscribe directly
              from the useEffect callback — `onSyncComplete` returns
              `() => boolean` (the Set.delete), which React treats as an
              invalid Destructor. Replaced with an explicit cleanup wrapper.
          Haptic feature:
            - `SyncBanner.tsx` now fires `Haptics.notificationAsync(Success)`
              on native right before the "تمت المزامنة · N عملية" toast so
              connected devices feel the moment their backlog landed. The
              toast provider also triggers Success haptic — our local call
              is a belt-and-suspenders guarantee for the sync moment.
          Owner (and accountant) home now uses the Header `tabs/tabValue
          /onTabChange` props to render 3 pill tabs INSIDE the dark navy area
          (Chats/Status/Calls style): "الرئيسية" / "التنبيهات" / "الأداء".
          - Home tab: ProBanner, OwnerOnboarding, stats grid (now with accent
            tone on today's sales), recent sales rows with coral avatar tone.
          - Alerts tab: AlertsCard, StaleDebtorsCard, low-stock warning section;
            empty state when nothing to show.
          - Performance tab: SalesTargetsCard + Leaderboard behind ProLock.
          Field-agent single-scroll preserved (no tabs) because its cards are
          flow-dependent (location, target, route, stock).
              INSIDE the dark area.
            - New `HeaderIconBtn` and `FAB` components.
            - Row component now supports `avatarText`/`avatarTone` for pastel
              circular avatars; cleaner divider; subtle pressed state.
            - Card: softer shadow, radius.lg, no border on light.
            - Stat: softer tile with pastel icon chip.
            - Badge/Section: refined.
          Header-right slots updated: NotificationBell + SyncBadge rendered as
          deep-navy pills with white icons; AccountButton is now a compact coral
          initials circle. Reports/legal/upgrade/agents-map screens migrated to
          the new `onBack` prop.
          _layout.tsx: StatusBar switched to `light` for the new dark header.
          Verified visually (login screen before/after and legal screen).
  - task: "Remove user-facing 'Convex' labels + dev artefacts"
    implemented: true
    working: "NA"
    file: "/app/frontend/app/convex-check.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Stripped every user-visible "Convex" string and raw function labels
          like "(stats.overview)" / "products.list · حيّ" from the diagnostic
          dashboard. Developer comments in TypeScript source still mention
          Convex as the backend provider — not user-visible.

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 4
  run_ui: true

test_plan:
  current_focus:
    - "Hash developer phone — DEVELOPER_PHONES_HASH"
    - "UI redesign — dark navy header, coral CTAs, rounded rows"
    - "Remove user-facing 'Convex' labels + dev artefacts"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Three changes to validate:
      (1) Backend: developer identification now uses hashed phone comparison
          (`DEVELOPER_PHONES_HASH` env var). Confirm `/api/auth/me` with
          `test_token_dev` still returns role=DEVELOPER (the role is persisted
          on the users row from the original seed); confirm `DEVELOPER_PHONES`
          is no longer referenced. All other APIs should be unaffected.
      (2) Frontend redesign: validate the new dark-navy curved header with
          centered title, back-button pill, coral primary CTAs with pill shape,
          and rounded list rows render across login, legal, upgrade, reports,
          activate, consent, and the owner/acct/agent dashboards. Nothing in
          the UI should still say "Convex" to the user.
      (3) Prefer visual + snapshot checks on web preview. Seeded tokens:
          test_token_owner/_acct/_agent/_dev (see /app/memory/test_credentials.md).

  - agent: "main"
    message: |
      Follow-up (iteration 5): scalable offline sync + owner-dashboard pill tabs.
      (A) `src/offline.ts` rewritten for high-throughput reconnect:
          - Bounded parallel sync (6 concurrent) across different endpoints
            while PRESERVING per-endpoint insertion order (same `path` is
            serialized). Dedupe by client-id on enqueue so re-enqueueing
            is a no-op.
          - Exponential backoff (1s→16s, 25% jitter, max 5 attempts) for
            transient failures (5xx/429/timeout/network). Backoff state is
            persisted on each item (`attempts`, `next_attempt_at`) so it
            survives app restarts.
          - Error classification: offline / transient / conflict / permanent.
            409 CONFLICT is treated as server-authoritative: we drop the
            optimistic row from any cached list that still has it, invalidate
            that endpoint's queries, and advance the queue (NO data loss —
            the user retains the failed-tray entry for review).
          - Progress tracking: `useSyncState().progress = { done, total }`;
            SyncBanner shows a progress bar + percentage for big flushes.
          - Per-request timeout in `api.ts` (25s AbortController) so hung
            sockets don't block the sync loop; aborts are retried.
          - New `retryFailed(id)` user action to move an item from failed
            tray back into the pending queue.
      (B) Owner-dashboard pill tabs: `src/screens/Overview.tsx` now renders
          the dark header with a 3-pill tab switcher inside (Chats/Status/Calls
          style) for OWNER + ACCOUNTANT: "الرئيسية" / "التنبيهات" / "الأداء".
          FIELD_AGENT keeps the single-scroll flow because its cards are
          flow-dependent. Stats row now uses accent (coral) + semantic tones.
      Please verify:
      - Backend regression suite (seeded tokens) still 100%.
      - A large simulated backlog (hundreds of items) flushes in parallel with
        no out-of-order writes against the same endpoint; a transient 503
        results in a retry (backoff visible in queue state), not an immediate
        failure.
      - 409 handler: a POST that returns 409 causes the optimistic cache row
        with that `id` to disappear and the pending queue to advance.
      - Owner home shows three pill tabs inside the dark navy header; the
        back-tab routing works (home/alerts/performance), and the "التنبيهات"
        tab shows alerts cards; "الأداء" shows targets + leaderboard behind
        ProLock. Agent home shows no tabs (single scroll preserved).
