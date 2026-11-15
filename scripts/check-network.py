"""Temporarily disconnect auth to demonstrate denial; always reconnect it."""
import json
import subprocess
import time
import urllib.error
import urllib.request


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def inspect(container):
    return json.loads(output("docker", "inspect", container))[0]["NetworkSettings"]["Networks"]


pg_ip = next(iter(inspect("pg-master").values()))["IPAddress"]
subprocess.run(["docker", "compose", "exec", "-T", "nginx", "sh", "-c",
                f"! nc -z -w 2 {pg_ip} 5432"], check=True)
auth = output("docker", "compose", "ps", "-q", "auth-service")
network = next(n for n in inspect(auth) if n.endswith("backend-net"))
try:
    subprocess.run(["docker", "network", "disconnect", network, auth], check=True)
    # Reload avoids waiting for cached addresses during the demonstration.
    subprocess.run(["docker", "compose", "exec", "-T", "nginx", "nginx", "-s", "reload"], check=True)
    time.sleep(2)
    try:
        urllib.request.urlopen("http://localhost/api/auth/health", timeout=15)
        raise AssertionError("Disconnected auth remained reachable")
    except urllib.error.HTTPError as error:
        assert error.code in (502, 504), error.code
        print(f"PASS: gateway cannot reach database or disconnected auth (HTTP {error.code})")
finally:
    subprocess.run(["docker", "network", "connect", "--alias", "auth-service", network, auth], check=True)
    subprocess.run(["docker", "compose", "exec", "-T", "nginx", "nginx", "-s", "reload"], check=True)
