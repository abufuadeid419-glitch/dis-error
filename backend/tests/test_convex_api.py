"""Backend tests for Convex HTTP API (Smart System)."""
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


# --- Health / root ---
class TestHealth:
    def test_api_root(self):
        r = requests.get(BASE_URL + "/", timeout=15)
        assert r.status_code == 200
        assert "Smart System" in r.text or "message" in r.json()


# --- Auth ---
class TestAuth:
    def test_me_without_token_401(self):
        r = requests.get(f"{BASE_URL}/auth/me", timeout=15)
        assert r.status_code == 401, f"got {r.status_code}: {r.text[:200]}"

    @pytest.mark.parametrize("role", list(TOKENS.keys()))
    def test_me_with_token_200(self, role):
        r = requests.get(f"{BASE_URL}/auth/me", headers=h(TOKENS[role]), timeout=15)
        assert r.status_code == 200, f"{role}: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert data is not None
        assert "role" in data or "user" in data or isinstance(data, dict)

    def test_otp_request_invalid_phone_400(self):
        r = requests.post(f"{BASE_URL}/auth/otp/request",
                          headers=h(), json={"phone": "123"}, timeout=20)
        assert r.status_code == 400, f"got {r.status_code}: {r.text[:200]}"
        body = r.json()
        assert "detail" in body
        # Arabic error message
        assert any(ord(c) > 127 for c in body["detail"]), f"Not Arabic: {body}"

    def test_otp_verify_without_phone_400(self):
        r = requests.post(f"{BASE_URL}/auth/otp/verify",
                          headers=h(), json={"phone": "", "code": ""}, timeout=15)
        assert r.status_code in (400, 401), f"got {r.status_code}: {r.text[:200]}"


# --- Read-only endpoints across roles ---
READ_ENDPOINTS_BY_ROLE = {
    "owner": ["/products", "/customers", "/sales", "/stats/overview",
              "/stats/agents", "/employees", "/notifications", "/org/profile"],
    "acct":  ["/products", "/customers", "/sales", "/stats/overview",
              "/collections", "/payment-vouchers", "/notifications"],
    "agent": ["/products", "/customers", "/my/inventory",
              "/routes/mine", "/notifications"],
    "dev":   ["/dev/stats", "/dev/licenses", "/dev/orgs", "/dev/monitoring",
              "/dev/versions"],
}


class TestReadOnlyEndpoints:
    @pytest.mark.parametrize("role,path", [
        (role, p) for role, paths in READ_ENDPOINTS_BY_ROLE.items() for p in paths
    ])
    def test_get(self, role, path):
        r = requests.get(BASE_URL + path, headers=h(TOKENS[role]), timeout=20)
        assert r.status_code in (200, 403), (
            f"{role} GET {path} -> {r.status_code} {r.text[:200]}"
        )
        # If 200, body must be JSON-decodable
        if r.status_code == 200:
            try:
                r.json()
            except Exception as e:
                pytest.fail(f"{role} GET {path} non-JSON: {e}")

    def test_unauthorized_products(self):
        r = requests.get(f"{BASE_URL}/products", timeout=15)
        assert r.status_code == 401

    def test_unknown_path_404(self):
        r = requests.get(f"{BASE_URL}/does-not-exist",
                         headers=h(TOKENS["owner"]), timeout=15)
        assert r.status_code == 404
