"""End-to-end demo check; creates a unique test user, order and server."""
import json
import os
import time
import uuid
import urllib.request

BASE = os.environ.get("BASE_URL", "http://localhost")
token = None


def request(path, data=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, headers=headers,
                                 data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


for route in ("auth", "products", "payment", "servers"):
    assert request(f"/api/{route}/health")["status"] == "ok"
credentials = {"email": f"smoke-{uuid.uuid4().hex}@example.com", "password": "Demo-password-123"}
token = request("/api/auth/register", credentials)["access_token"]
token = request("/api/auth/login", credentials)["access_token"]
user = request("/api/auth/me")
assert user["email"] == credentials["email"]
plans = request("/api/products/plans")
assert plans == request("/api/products/plans") and len(plans) == 3
order = request("/api/products/order", {"plan_id": plans[0]["id"]})
assert order["status"] == "pending"
assert request("/api/payment/pay", {"order_id": order["id"]})["status"] == "paid"
deadline = time.monotonic() + 60
while time.monotonic() < deadline:
    server = next(s for s in request("/api/servers/") if s["id"] == order["server_id"])
    if server["status"] == "active":
        break
    time.sleep(1)
else:
    raise AssertionError("Provisioning did not finish within 60 seconds")
assert server["ip_address"] and server["root_password"] and server["hostname"]
for action, expected in (("stop", "stopped"), ("start", "active"), ("reboot", "active")):
    assert request(f"/api/servers/{server['id']}/{action}", {})["status"] == expected
request(f"/api/servers/{server['id']}/reset-password", {})
updated = next(s for s in request("/api/servers/") if s["id"] == server["id"])
assert updated["root_password"] != server["root_password"]
print(f"PASS: user={user['id']}, order={order['id']}, server={server['id']}")
