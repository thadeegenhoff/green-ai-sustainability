import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class StackConfigurationTests(unittest.TestCase):
    def test_dashboard_provider_uses_grafana_directory(self):
        provider = ROOT / "grafana/provisioning/dashboards/dashboards.yml"
        config = yaml.safe_load(provider.read_text())
        self.assertEqual(config["providers"][0]["options"]["path"], "/var/lib/grafana/dashboards")

    def test_every_dashboard_resolves_the_provisioned_data_source(self):
        config = yaml.safe_load((ROOT / "grafana/provisioning/datasources/influxdb.yml").read_text())
        expected = config["datasources"][0]["uid"]
        refs = []

        def walk(value):
            if isinstance(value, dict):
                if isinstance(value.get("datasource"), dict):
                    refs.append(value["datasource"].get("name"))
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        dashboards = list((ROOT / "grafana/dashboards").glob("*.json"))
        self.assertEqual(len(dashboards), 3)
        for path in dashboards:
            dashboard = json.loads(path.read_text())
            walk(dashboard)
            self.assertTrue(any(v["spec"]["name"] == "bucket" for v in dashboard["spec"]["variables"]))
        self.assertTrue(refs)
        self.assertEqual(set(refs) - {"-- Grafana --"}, {expected})

    def test_flow_and_container_share_environment_configuration(self):
        compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        service = compose["services"]["nodered"]
        self.assertIn("build", service)
        self.assertIn("INFLUXDB_ORG", service["environment"])
        self.assertIn("INFLUXDB_BUCKET", service["environment"])
        flow = json.loads((ROOT / "nodered/flows.json").read_text())
        outputs = [node for node in flow if node["type"] == "influxdb out"]
        self.assertTrue(outputs)
        for node in outputs:
            self.assertEqual(node["org"], "${INFLUXDB_ORG}")
            self.assertEqual(node["bucket"], "${INFLUXDB_BUCKET}")
        inject = next(node for node in flow if node["type"] == "inject")
        self.assertTrue(inject["d"])
        co2_output = next(node for node in outputs if node["measurement"] == "grid_carbon_intensity")
        transform = next(node for node in flow if node.get("name") == "Transform CO2")
        self.assertIn(co2_output["id"], transform["wires"][0])


if __name__ == "__main__":
    unittest.main()
