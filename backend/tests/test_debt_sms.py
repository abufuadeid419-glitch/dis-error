"""Tests for new /org/debt-sms endpoint + regression on /auth/me and /stats/reports."""
import pytest
import requests

BASE_URL = "https://fearless-ostrich-878.eu-west-1.convex.site/api"

TOKENS = {
    "dev": "test_token_dev",
    "owner": "test_token_owner",
    "acct": "test_token_acct",
    "agent": "test_token_agent",
}


def h(token=None):
    hdr = {"Content-Type": "application/json"}
    if token:
        hdr["Authorization"] = f"Bearer {token}"
    return hdr


# --- Regression: /auth/me across all 4 tokens ---
class TestAuthMeRegression:
    @pytest.mark.parametrize("role", list(TOKENS.keys()))
    def test_me_all_tokens(self, role):
        r = requests.get(f"{BASE_URL}/auth/me", headers=h(TOKENS[role]), timeout=15)
        assert r.status_code == 200, f"{role}: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert isinstance(data, dict)


# --- Regression: /stats/reports?period=week for LICENSE org not locked ---
class TestStatsReports:
    def test_reports_week_owner_not_locked(self):
        r = requests.get(
            f"{BASE_URL}/stats/reports?period=week",
            headers=h(TOKENS["owner"]), timeout=20,
        )
        assert r.status_code == 200, f"owner reports week -> {r.status_code} {r.text[:300]}"
        try:
            data = r.json()
        except Exception as e:
            pytest.fail(f"non-JSON response: {e}")
        assert isinstance(data, (dict, list))


# --- New: /org/debt-sms ---
class TestDebtSmsGet:
    def test_get_owner_200_shape(self):
        r = requests.get(f"{BASE_URL}/org/debt-sms",
                         headers=h(TOKENS["owner"]), timeout=15)
        assert r.status_code == 200, f"owner GET -> {r.status_code} {r.text[:300]}"
        body = r.json()
        assert isinstance(body, dict)
        for key in ("enabled", "days", "eligible", "sample"):
            assert key in body, f"missing {key} in {body}"
        assert isinstance(body["enabled"], bool)
        assert body["days"] in (7, 14, 30)

    def test_get_without_token_401(self):
        r = requests.get(f"{BASE_URL}/org/debt-sms", timeout=15)
        assert r.status_code == 401, f"got {r.status_code} {r.text[:200]}"

    @pytest.mark.parametrize("role", ["acct", "agent"])
    def test_get_non_owner_403(self, role):
        r = requests.get(f"{BASE_URL}/org/debt-sms",
                         headers=h(TOKENS[role]), timeout=15)
        assert r.status_code == 403, f"{role} GET -> {r.status_code} {r.text[:200]}"


class TestDebtSmsPut:
    @pytest.mark.parametrize("days", [7, 14, 30])
    def test_put_owner_valid_days(self, days):
        r = requests.put(
            f"{BASE_URL}/org/debt-sms",
            headers=h(TOKENS["owner"]),
            json={"enabled": True, "days": days}, timeout=15,
        )
        assert r.status_code == 200, f"days={days} -> {r.status_code} {r.text[:300]}"
        # Verify persistence via GET
        g = requests.get(f"{BASE_URL}/org/debt-sms",
                         headers=h(TOKENS["owner"]), timeout=15)
        assert g.status_code == 200
        got = g.json()
        assert got["enabled"] is True
        assert got["days"] == days

    def test_put_owner_disable(self):
        r = requests.put(
            f"{BASE_URL}/org/debt-sms",
            headers=h(TOKENS["owner"]),
            json={"enabled": False, "days": 7}, timeout=15,
        )
        assert r.status_code == 200
        g = requests.get(f"{BASE_URL}/org/debt-sms",
                         headers=h(TOKENS["owner"]), timeout=15).json()
        assert g["enabled"] is False

    def test_put_invalid_days_400(self):
        r = requests.put(
            f"{BASE_URL}/org/debt-sms",
            headers=h(TOKENS["owner"]),
            json={"enabled": True, "days": 5}, timeout=15,
        )
        assert r.status_code == 400, f"got {r.status_code} {r.text[:200]}"

    def test_put_non_owner_403(self):
        r = requests.put(
            f"{BASE_URL}/org/debt-sms",
            headers=h(TOKENS["acct"]),
            json={"enabled": True, "days": 7}, timeout=15,
        )
        assert r.status_code == 403, f"got {r.status_code} {r.text[:200]}"

    def test_put_without_token_401(self):
        r = requests.put(
            f"{BASE_URL}/org/debt-sms",
            headers=h(),
            json={"enabled": True, "days": 7}, timeout=15,
        )
        assert r.status_code == 401
