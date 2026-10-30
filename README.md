# Green AI Sustainability Stack

This independent Docker Compose stack collects physical-host electricity readings and provides the measurement interface for [green-ai-orchestrator](https://github.com/thadeegenhoff/green-ai-orchestrator). Shelly plugs send MQTT readings to Mosquitto; Node-RED normalises them into InfluxDB; Grafana displays measurements and experiment results.

| Service | Purpose | Host port |
|---|---|---|
| Mosquitto | MQTT transport | 1883 |
| InfluxDB 2 | Measurements and experiment results | 8086 |
| Node-RED | Ingestion and optional carbon-intensity input | 1880 |
| Grafana | Device, training and inference dashboards | 3000 |

## 1. Configure and start

Docker Engine and the Docker Compose plugin are required. Use an isolated local network and ensure the ports are available.

```bash
git clone https://github.com/thadeegenhoff/green-ai-sustainability.git
cd green-ai-sustainability
cp .env.example .env
# Edit the passwords, token, organisation and bucket in .env.
docker compose up -d --build
docker compose ps
```

On PowerShell, use `Copy-Item .env.example .env` for the copy step. Keep `.env` outside Git.

The Node-RED image installs `node-red-contrib-influxdb@0.7.0` outside `/data`, so a persistent data volume does not hide the dependency. A new Node-RED volume is populated with the supplied flow. An existing volume retains its own flow; import `nodered/flows.json` manually if you want to update that installation. Existing data volumes are not deleted or migrated by these instructions.

The release defaults select Node-RED 4.1.0 and Grafana 13.0.1, with InfluxDB 2 and Mosquitto 2. Grafana must support the included v2 resource dashboard format. The defaults are configurable through `.env`; after a successful deployment, retain exact image digests for a fully fixed environment. They are not a claim about the exact versions used in every historical experiment.

Open `http://localhost:1880` (Node-RED), `http://localhost:8086` (InfluxDB) and `http://localhost:3000` (Grafana).

## 2. Configure the Node-RED InfluxDB token

The flow's organisation and bucket fields use `${INFLUXDB_ORG}` and `${INFLUXDB_BUCKET}`, supplied to the container by Compose. The token is deliberately not stored in the exported flow.

1. Open Node-RED and edit an InfluxDB output node.
2. Open its shared `GreenAIDB` configuration node with the pencil button.
3. Use InfluxDB version 2.0, URL `http://influxdb:8086`, and the token from `INFLUXDB_ADMIN_TOKEN` in your local `.env`.
4. Save and deploy. Confirm the InfluxDB nodes have no credential or unknown-node errors.

This one-time credential entry is required on a fresh installation. Changing `.env` alone does not replace credentials already saved in a Node-RED volume.

## 3. Connect the physical meters

Configure each Shelly to send MQTT to `<MEASUREMENT-HOST-IP>:1883`, using a stable unique device prefix. Example prefixes are `orchestrator`, `pc`, `oldlaptop`, `rpi5-8gb` and `rpi5-16gb`.

The flow stores power in measurement `shelly_plug`, field `power_w`, with `device`, `source` and `generation` tags. Null, empty and non-numeric power values are not converted into zero power. The device tag must exactly match `power_tag_value` in the orchestrator's `node_mapping.json`.

Verify that readings arrive before an AI experiment. A separate synthetic transport probe can be sent without impersonating a physical device:

```bash
docker compose exec -T mosquitto mosquitto_pub -h localhost \
  -t 'greenai-probe/status/switch:0' -m '{"apower":17.5}'
```

Look for device `greenai-probe` in InfluxDB. This is a pipeline check, not a calibrated meter observation or experiment result.

## 4. Open the dashboards

The provider is under `grafana/provisioning/dashboards/dashboards.yml` (lowercase). Grafana provisions the InfluxDB data source with stable UID `greenai-influxdb`; all three dashboard exports reference it.

Dashboards are loaded from `grafana/dashboards/` into the **Green AI** folder. Their bucket selector defaults to `greenaidata`. If `INFLUXDB_BUCKET` differs, select that bucket in each dashboard; dashboard JSON does not automatically substitute Compose environment variables. Training and inference views will remain empty until the orchestrator writes results.

## 5. Connect the orchestrator

Configure the orchestrator's local `.env.influx` with matching values:

```bash
INFLUX_URL=http://<MEASUREMENT-HOST-IP>:8086
INFLUX_ORG=greenai
INFLUX_BUCKET=greenaidata
INFLUX_TOKEN=<the-token-from-your-local-env>
POWER_MEASUREMENT=shelly_plug
POWER_FIELD=power_w
POWER_NODE_TAG=device
```

Replace the host, organisation and bucket as needed. `http://influxdb:8086` works inside the Compose network; another host or VM needs the reachable measurement-host address. Continue with cluster preparation, image build, a small training run and inference in the orchestrator README.

## Optional carbon intensity

The Electricity Maps inject node remains disabled. To use it, configure `ELECTRICITY_MAPS_TOKEN` and `ELECTRICITY_MAPS_ZONE` locally, check the API response and then enable the node. Its output uses measurement `grid_carbon_intensity` in the same configured bucket. Enabling this path does not validate dynamic emissions calculations or reproduce the fixed-factor historical results.

## Validation

```bash
python -m pip install pyyaml
python -m unittest discover -s tests -v
node tests/test_flow.js
```

For an isolated fresh stack with local `.env` and services running, `python tests/smoke_stack.py` checks service readiness, provisions the Node-RED test credentials through its local admin API, publishes a separate MQTT probe, verifies its InfluxDB value and checks Grafana provisioning. It uses local URLs and should be run only against the disposable test stack. CI runs this smoke check with temporary volumes.

## Operations and scope

Use `docker compose logs -f` for diagnostics and `docker compose stop` to stop services. `docker compose down` removes containers while retaining volumes. Removing volumes deletes database and Node-RED state; it is not needed to install these changes.

The MQTT demo allows anonymous access, and Node-RED has no production authentication policy. Keep the stack on a trusted local network. Original experiment databases and result bundles are not included.

## License

Copyright 2026 Thade Egenhoff.

Except where otherwise noted, the original code, configuration files, Node-RED flows, dashboards and documentation in this repository are licensed under the [Apache License, Version 2.0](LICENSE) (`Apache-2.0`). See [NOTICE](NOTICE) for attribution information.

Third-party software, container images and external data retain their respective licences.
