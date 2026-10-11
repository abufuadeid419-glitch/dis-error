"""OTP verify with force field — must return Arabic error when no OTP requested."""
import requests
BASE_URL = "https://fearless-ostrich-878.eu-west-1.convex.site/api"

def test_otp_verify_with_force_no_otp_requested():
    r = requests.post(f"{BASE_URL}/auth/otp/verify",
                      json={"phone": "+963900999999", "code": "123456", "force": True},
                      timeout=20)
    assert r.status_code in (400, 401), f"got {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "detail" in body
    # Expect Arabic 'اطلب رمز تحقق أولاً'
    assert "اطلب" in body["detail"] or "رمز" in body["detail"], f"Not expected Arabic: {body}"

def test_otp_verify_force_false_also_rejected():
    r = requests.post(f"{BASE_URL}/auth/otp/verify",
                      json={"phone": "+963900999998", "code": "000000", "force": False},
                      timeout=20)
    assert r.status_code in (400, 401)
