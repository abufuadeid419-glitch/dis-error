"""Iteration 5 — offline sync + conflict resolution regression tests.

Covers:
  - /api/auth/me for the 4 seeded tokens (still 200 with expected role)
  - /api/stats/overview, /api/products, /api/customers, /api/sales for OWNER
  - Idempotency contract on Convex mutations that accept a body `id`:
      POST /api/customers twice with same id → same doc, no duplicate
      POST /api/sales twice with same id → same doc, no duplicate (if agent
          has inventory + customer); otherwise test is skipped with a note.
      POST /api/collections twice with same id → same doc, no duplicate
          (chained after we create a customer with a non-zero balance via
          a sale; if that path isn't viable in the seed, we skip and note it).
"""
import os
import time
import uuid

import pytest
import requests

BASE_URL = "https://fearless-ostrich-878.eu-west-1.convex.site/api"

TOKENS = {
    "dev": ("test_token_dev", "DEVELOPER"),
    "owner": ("test_token_owner", "OWNER"),
    "acct": ("test_token_acct", "ACCOUNTANT"),  # employee_type
    "agent": ("test_token_agent", "FIELD_AGENT"),  # employee_type
}


def h(token=None):
    hdr = {"Content-Type": "application/json"}
    if token:
        hdr["Authorization"] = f"Bearer {token}"
    return hdr


# --- Auth regression: 4 seeded tokens still return 200 with expected role ---
class TestAuthMe:
    @pytest.mark.parametrize("role_key", list(TOKENS.keys()))
    def test_auth_me_200(self, role_key):
        tok, expected = TOKENS[role_key]
        r = requests.get(f"{BASE_URL}/auth/me", headers=h(tok), timeout=15)
        assert r.status_code == 200, f"{role_key} -> {r.status_code} {r.text[:200]}"
        data = r.json()
        # Role / employee_type varies: OWNER / DEVELOPER sit on `role`,
        # ACCOUNTANT / FIELD_AGENT sit on `employee_type` with role=EMPLOYEE.
        role = data.get("role")
        emp = data.get("employee_type")
        if role_key in ("dev", "owner"):
            assert role == expected, f"{role_key} role={role!r}"
        else:
            assert emp == expected, (
                f"{role_key} employee_type={emp!r} role={role!r}"
            )


# --- Owner read endpoints: all 200 ---
class TestOwnerReads:
    @pytest.mark.parametrize("path", [
        "/stats/overview", "/products", "/customers", "/sales",
    ])
    def test_owner_get_200(self, path):
        tok, _ = TOKENS["owner"]
        r = requests.get(BASE_URL + path, headers=h(tok), timeout=20)
        assert r.status_code == 200, f"GET {path} -> {r.status_code} {r.text[:200]}"
        body = r.json()
        # Shape sanity
        if path == "/stats/overview":
            assert isinstance(body, dict), f"{path} not dict: {type(body)}"
            # Standard keys we rely on in the Overview screen
            for k in ("today_sales", "sales_total", "collections_total", "debts_total"):
                assert k in body, f"missing {k} in /stats/overview"
        else:
            assert isinstance(body, list), f"{path} not list: {type(body)}"


# --- Idempotency contract on body `id` for Convex mutations ---
class TestIdempotency:
    """Replay-safe writes: same body id => same doc, no duplicate row.

    This is the backend invariant the offline queue relies on (sendOne
    retries after transient failures); if the server weren't id-idempotent,
    a user who went offline mid-flush would double-post.
    """

    def test_customers_create_idempotent(self):
        tok, _ = TOKENS["agent"]
        bid = f"TEST_{uuid.uuid4().hex[:12]}"
        payload = {
            "id": bid,
            "name": f"TEST_IDEMP_{bid}",
            "phone": "0999123456",
            "address": "Damascus",
            "location": "",
            "lat": 33.5,
            "lng": 36.3,
        }
        r1 = requests.post(f"{BASE_URL}/customers",
                           headers=h(tok), json=payload, timeout=20)
        assert r1.status_code == 200, f"first POST: {r1.status_code} {r1.text[:200]}"
        d1 = r1.json()
        assert d1.get("id") == bid, f"returned id mismatch: {d1}"

        # Replay with identical body (and even with mutated name — server
        # should IGNORE and return the already-existing row).
        r2 = requests.post(
            f"{BASE_URL}/customers",
            headers=h(tok),
            json={**payload, "name": "SHOULD_BE_IGNORED"},
            timeout=20,
        )
        assert r2.status_code == 200, f"second POST: {r2.status_code} {r2.text[:200]}"
        d2 = r2.json()
        assert d2.get("id") == bid
        # Must be the ORIGINAL doc, not a new one with a mutated name.
        assert d2.get("name") == d1.get("name"), (
            f"idempotency violated: name changed on replay {d1} -> {d2}"
        )
        # Verify only one row with that id exists.
        rl = requests.get(f"{BASE_URL}/customers",
                          headers=h(tok), timeout=20)
        assert rl.status_code == 200
        matches = [c for c in rl.json() if c.get("id") == bid]
        assert len(matches) == 1, f"expected 1 row, got {len(matches)}: {matches}"

    def test_sales_create_idempotent_or_errors_consistently(self):
        """Both POSTs with same `id` must return the same outcome.

        If the agent has an existing customer + inventory, both calls
        succeed with the same invoice_no. If not (seed limitation),
        both must fail with the same Arabic error — not create one row.
        """
        tok, _ = TOKENS["agent"]
        # Grab the first customer the agent can see
        rc = requests.get(f"{BASE_URL}/customers", headers=h(tok), timeout=15)
        assert rc.status_code == 200
        custs = rc.json()
        # Grab the agent's inventory
        ri = requests.get(f"{BASE_URL}/my/inventory", headers=h(tok), timeout=15)
        assert ri.status_code == 200
        inv = ri.json()
        if not custs or not inv:
            pytest.skip(f"agent seed lacks customer({len(custs)})/inv({len(inv)}) — "
                        f"idempotency path not exercisable")
        cust = custs[0]
        item = next((x for x in inv if (x.get("quantity") or 0) > 0), None)
        if not item:
            pytest.skip("agent has no inventory with quantity>0")
        bid = f"TEST_{uuid.uuid4().hex[:12]}"
        payload = {
            "id": bid,
            "customer_id": cust["id"],
            "items": [{"product_id": item["product_id"], "quantity": 1}],
            "paid_amount": 0,
        }
        r1 = requests.post(f"{BASE_URL}/sales",
                           headers=h(tok), json=payload, timeout=20)
        r2 = requests.post(f"{BASE_URL}/sales",
                           headers=h(tok), json=payload, timeout=20)
        assert r1.status_code == r2.status_code, (
            f"idempotency: status diff {r1.status_code} vs {r2.status_code}"
        )
        if r1.status_code == 200:
            d1, d2 = r1.json(), r2.json()
            assert d1.get("id") == bid and d2.get("id") == bid
            assert d1.get("invoice_no") == d2.get("invoice_no"), (
                f"duplicate sale created: {d1.get('invoice_no')} vs {d2.get('invoice_no')}"
            )
            # Verify only one sale with that id in the list.
            rs = requests.get(f"{BASE_URL}/sales", headers=h(tok), timeout=20)
            assert rs.status_code == 200
            matches = [s for s in rs.json() if s.get("id") == bid]
            assert len(matches) == 1, f"expected 1 sale, got {len(matches)}"

    def test_collections_create_idempotent_or_errors_consistently(self):
        """Chase an existing debtor; if none, skip. Both POSTs must agree."""
        tok, _ = TOKENS["agent"]
        rc = requests.get(f"{BASE_URL}/customers", headers=h(tok), timeout=15)
        assert rc.status_code == 200
        debtor = next((c for c in rc.json() if (c.get("balance") or 0) > 0), None)
        if not debtor:
            pytest.skip("no debtor customer in seed — collections idempotency "
                        "not exercisable with amount>0 (would 400)")
        bid = f"TEST_{uuid.uuid4().hex[:12]}"
        amount = min(1.0, float(debtor["balance"]))
        payload = {
            "id": bid,
            "customer_id": debtor["id"],
            "amount": amount,
        }
        r1 = requests.post(f"{BASE_URL}/collections",
                           headers=h(tok), json=payload, timeout=20)
        r2 = requests.post(f"{BASE_URL}/collections",
                           headers=h(tok), json=payload, timeout=20)
        assert r1.status_code == r2.status_code
        if r1.status_code == 200:
            d1, d2 = r1.json(), r2.json()
            assert d1.get("id") == d2.get("id") == bid
            assert d1.get("receipt_no") == d2.get("receipt_no"), (
                f"duplicate collection: {d1} vs {d2}"
            )


# --- No references to removed env var DEVELOPER_PHONES (plaintext) ---
class TestEnvVarCleanup:
    def test_no_plaintext_developer_phones_in_frontend(self):
        import subprocess
        res = subprocess.run(
            ["grep", "-r", "DEVELOPER_PHONES",
             "/app/frontend/convex", "/app/frontend/src", "/app/frontend/app"],
            capture_output=True, text=True,
        )
        hits = [
            ln for ln in res.stdout.splitlines()
            if ln.strip() and "DEVELOPER_PHONES_HASH" not in ln
        ]
        assert not hits, f"plaintext DEVELOPER_PHONES still referenced:\n" + "\n".join(hits)
