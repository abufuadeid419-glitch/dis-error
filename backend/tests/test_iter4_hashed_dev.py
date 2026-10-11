"""Iteration 4 — verify (a) hashed developer phone keeps role=DEVELOPER
on the dev test token, (b) smoke-test other read endpoints, (c) OTP send
to the Syrian +9639 phone still routes through the Arabic SMS-gateway
error path (hashing change must NOT affect the OTP send contract)."""

import pytest
import requests

BASE_URL = "https://fearless-ostrich-878.eu-west-1.convex.site/api"

TOKENS = {
    "dev": "test_token_dev",
    "owner": "test_token_owner",
    "acct": "test_token_acct",
    "agent": "test_token_agent",
}


def _h(token=None):
    hdr = {"Content-Type": "application/json"}
    if token:
        hdr["Authorization"] = f"Bearer {token}"
    return hdr


# -------- Hashed developer identity --------
class TestDevRolePersistence:
    def test_dev_token_me_has_developer_role(self):
        r = requests.get(f"{BASE_URL}/auth/me", headers=_h(TOKENS["dev"]), timeout=15)
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:200]}"
        body = r.json()
        # Role may be on body["role"] or body["user"]["role"]
        role = body.get("role") or (body.get("user") or {}).get("role")
        assert role == "DEVELOPER", f"expected DEVELOPER, got {role}: {body}"


# -------- Smoke tests for seeded tokens --------
class TestOwnerReads:
    def test_stats_overview_owner(self):
        r = requests.get(f"{BASE_URL}/stats/overview", headers=_h(TOKENS["owner"]), timeout=15)
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        d = r.json()
        for k in ("sales_total", "today_sales", "collections_total", "debts_total", "products", "customers"):
            assert k in d, f"missing {k} in {list(d.keys())}"

    def test_products_list_owner(self):
        # HTTP route is /products (api.products.list is the internal Convex query name).
        r = requests.get(f"{BASE_URL}/products", headers=_h(TOKENS["owner"]), timeout=15)
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        assert isinstance(r.json(), list)

    def test_notifications_list_owner(self):
        r = requests.get(f"{BASE_URL}/notifications", headers=_h(TOKENS["owner"]), timeout=15)
        assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
        body = r.json()
        assert isinstance(body, dict) and "items" in body, f"unexpected: {body}"
        assert isinstance(body["items"], list)


class TestAcctAgentMe:
    @pytest.mark.parametrize("role", ["acct", "agent"])
    def test_me_200_with_role(self, role):
        r = requests.get(f"{BASE_URL}/auth/me", headers=_h(TOKENS[role]), timeout=15)
        assert r.status_code == 200, f"{role}: {r.status_code} {r.text[:200]}"
        body = r.json()
        resolved = body.get("role") or (body.get("user") or {}).get("role")
        assert resolved in ("OWNER", "EMPLOYEE", "DEVELOPER"), f"{role}: role={resolved} body={body}"


# -------- OTP send still Arabic-errors on real Syrian phone (SMS gateway not reachable) --------
class TestOtpArabicErrorPath:
    def test_otp_request_syrian_phone_arabic_error_or_ok(self):
        """Hashing change must NOT break the OTP contract; the SMS gateway
        either succeeds (200/{"ok": true}) OR returns a 4xx/5xx with an
        Arabic error string. The point: non-5xx /infra/ failure (no stack
        trace about missing env var)."""
        r = requests.post(
            f"{BASE_URL}/auth/otp/request",
            headers=_h(),
            json={"phone": "+963900000777"},  # not in dev list; triggers SMS send
            timeout=30,
        )
        # Must not be a 500 with python/js stack trace
        assert r.status_code in (200, 400, 401, 403, 422, 429, 502), f"unexpected {r.status_code}: {r.text[:300]}"
        if r.status_code != 200:
            body = r.json()
            msg = body.get("detail") or body.get("error") or ""
            # Should contain non-ASCII (Arabic) chars
            assert any(ord(c) > 127 for c in msg), f"expected Arabic error, got: {msg!r}"

    def test_otp_request_rejects_bad_phone_shape(self):
        r = requests.post(
            f"{BASE_URL}/auth/otp/request",
            headers=_h(),
            json={"phone": "0963900000777"},  # missing +
            timeout=15,
        )
        assert r.status_code == 400, f"{r.status_code} {r.text[:200]}"
        body = r.json()
        msg = body.get("detail") or body.get("error") or ""
        assert any(ord(c) > 127 for c in msg)
