"""Integration check for a disposable, locally running Compose test stack."""

import base64
import json
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def request(url, payload=None, headers=None):
    body = json.dumps(payload).encode() if payload is not None else None
    merged = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        merged["Content-Type"] = "application/json"
    with urlopen(Request(url, data=body, headers=merged), timeout=10) as response:
        return response.read().decode()


def wait_for(callback, label):
    for _ in range(60):
        try:
            value = callback()
            if value:
                return value
        except (HTTPError, URLError, TimeoutError, AssertionError):
            pass
        time.sleep(2)
    raise AssertionError(f"Timed out waiting for {label}")


def main():
    # Local test credentials are read without writing them to logs or the repo.
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")

    wait_for(lambda: json.loads(request("http://localhost:8086/health"))["status"] == "pass", "InfluxDB")
    wait_for(lambda: request("http://localhost:1880/flows"), "Node-RED")
    flow = json.loads(request("http://localhost:1880/flows"))
    assert any(node["type"] == "mqtt in" for node in flow), "Supplied flow was not seeded"
    modules = request("http://localhost:1880/nodes")
    assert "node-red-contrib-influxdb" in modules, "InfluxDB nodes were not installed"
    for node in flow:
        if node["type"] == "influxdb":
            node["credentials"] = {"token": env["INFLUXDB_ADMIN_TOKEN"]}
    request("http://localhost:1880/flows", flow, {"Node-RED-Deployment-Type": "full"})

    probe = f"ci-probe-{int(time.time())}"
    query = (
        f'from(bucket: "{env["INFLUXDB_BUCKET"]}") |> range(start: -5m) '
        f'|> filter(fn: (r) => r._measurement == "shelly_plug" and '
        f'r._field == "power_w" and r.device == "{probe}")'
    )

    def observe_probe():
        subprocess.run([
            "docker", "compose", "exec", "-T", "mosquitto", "mosquitto_pub",
            "-h", "localhost", "-t", f"{probe}/status/switch:0", "-m", '{"apower":17.5}',
        ], cwd=ROOT, check=True, capture_output=True)
        csv = request(
            "http://localhost:8086/api/v2/query?" + urlencode({"org": env["INFLUXDB_ORG"]}),
            {"query": query, "type": "flux"},
            {"Authorization": "Token " + env["INFLUXDB_ADMIN_TOKEN"], "Accept": "text/csv"},
        )
        return probe in csv and "17.5" in csv

    wait_for(observe_probe, "MQTT → Node-RED → InfluxDB probe")

    auth = base64.b64encode(
        f'{env["GRAFANA_ADMIN_USER"]}:{env["GRAFANA_ADMIN_PASSWORD"]}'.encode()
    ).decode()
    headers = {"Authorization": "Basic " + auth}
    wait_for(lambda: json.loads(request("http://localhost:3000/api/health"))["database"] == "ok", "Grafana")
    source = json.loads(request("http://localhost:3000/api/datasources/uid/greenai-influxdb", headers=headers))
    assert source["uid"] == "greenai-influxdb"
    dashboards = wait_for(
        lambda: json.loads(request("http://localhost:3000/api/search?type=dash-db", headers=headers)),
        "provisioned dashboards",
    )
    assert len(dashboards) >= 3, "Expected three provisioned dashboards"
    print("Stack smoke check passed: ingestion, extra Node-RED nodes and Grafana provisioning.")


if __name__ == "__main__":
    main()
