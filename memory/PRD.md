# النظام الذكي (Smart System) — Cloned App

## Original Problem Statement
Clone the mobile app from https://github.com/abufuadeid419-glitch/apk-ios-code.git and wire it to the owner's existing Convex deployment.

## Architecture
- **Frontend**: Expo Router (React Native), Arabic RTL (forced), Cairo font family. ~30 screens across 4 role areas: `owner/`, `acct/` (accountant), `dist` (distributor/field agent), `dev/` (developer). Uses `@tanstack/react-query`, offline sync queue, Bluetooth receipt printing, maps/GPS tracking, QR scan.
- **Backend**: Convex (external BaaS). All REST logic in `frontend/convex/*.ts`, served from the deployment's HTTP `.site` domain under `/api/...`. The FastAPI `backend/server.py` is a health-check stub only (no MongoDB).
- **Convex deployment**: `fearless-ostrich-878` (eu-west-1).
  - `EXPO_PUBLIC_CONVEX_URL=https://fearless-ostrich-878.eu-west-1.convex.cloud`
  - `EXPO_PUBLIC_CONVEX_SITE_URL=https://fearless-ostrich-878.eu-west-1.convex.site`
- **Auth**: Phone + SMS OTP via SMS Gateway (sms-gate.app). Credentials (`SMS_GATE_USERNAME`, `SMS_GATE_PASSWORD`, `OTP_PEPPER`, `DEVELOPER_PHONES_HASH`) live server-side in Convex deployment env — not in app code. No WhatsApp fallback; clear error on SMS failure.

## User Personas
- **Owner (OWNER)**: dashboard, customers, products, sales, reports, employees, Pro plan.
- **Distributor / Field Agent (EMPLOYEE/FIELD_AGENT)**: route, deliveries, new sale, collections, map tracking.
- **Accountant (EMPLOYEE/ACCOUNTANT)**: sales, customers, debts, collections.
- **Developer (DEVELOPER)**: orgs, licenses, billing (super-admin).

## Core Requirements (static)
- Arabic RTL interface preserved exactly.
- All 4 roles functional against live Convex data.
- Offline-first sync with reconnect queue drain.
- Pro subscription tiers (trial → free fallback → paid lock).

## Implemented (dates)
- 2026-06: Cloned full repo into workspace; wired frontend to owner's live Convex deployment via env vars; preserved platform-protected env vars. Verified: app boots to Arabic login screen, Convex `/api` reachable, `/api/auth/me` returns 401 unauthenticated (auth routing OK), FastAPI stub healthy.

## Notes / Backlog (P1/P2)
- Native-only features (Bluetooth printing, camera QR scan, background GPS, haptics) require a real device build — not testable in Expo Go / web preview.
- Full E2E testing agent intentionally skipped to avoid mutating live production data and incurring real SMS charges.
- Phone field accepts any country code (e.g. +123) without validation before send — small hardening opportunity.
