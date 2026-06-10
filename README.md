# GreenAI Sustainability

Kurze Docker-Compose-Umgebung zur Erfassung und Visualisierung von Energie- und CO₂-Daten für die GreenAI-Demonstration.

Die Umgebung läuft getrennt vom GreenAI-Orchestrator und stellt Messdaten zentral über InfluxDB bereit. Shelly-Steckdosen senden ihre Leistungsdaten per MQTT an Mosquitto. Node-RED verarbeitet die MQTT-Nachrichten und schreibt die Messwerte nach InfluxDB. Grafana liest die Daten aus InfluxDB und visualisiert sie in Dashboards.

## Enthaltene Dienste

| Dienst | Zweck | Port |
|---|---|---:|
| Mosquitto | MQTT-Broker für Shelly-/IoT-Messwerte | `1883` |
| InfluxDB 2 | Zeitreihendatenbank für Energie-, CO₂- und Experimentdaten | `8086` |
| Node-RED | Verarbeitung der MQTT-Daten und optionaler CO₂-API-Abfragen | `1880` |
| Grafana | Visualisierung der Messdaten | `3000` |

## Repository-Struktur

```text
green-ai-sustainability/
├── docker-compose.yml
├── .env.example
├── grafana/provisioning/datasources/influxdb.yml
├── mosquitto/config/mosquitto.conf
└── nodered/flows.json
```

## Schnellstart

```bash
git clone https://gitup.uni-potsdam.de/egenhoff/green-ai-sustainability.git
cd green-ai-sustainability
cp .env.example .env
```

Unter Windows PowerShell alternativ:

```powershell
Copy-Item .env.example .env
notepad .env
```

Trage in `.env` lokale Werte für InfluxDB, Grafana und optional Electricity Maps ein. Beispiel:

```env
TZ=Europe/Berlin
INFLUXDB_USERNAME=admin
INFLUXDB_PASSWORD=change_me
INFLUXDB_ORG=thade
INFLUXDB_BUCKET=greenaidata
INFLUXDB_ADMIN_TOKEN=change_me
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change_me
ELECTRICITY_MAPS_TOKEN=optional
ELECTRICITY_MAPS_ZONE=DE
```

Dann starten:

```bash
docker compose up -d
docker compose ps
```

Dienste öffnen:

```text
Grafana:  http://localhost:3000
InfluxDB: http://localhost:8086
Node-RED: http://localhost:1880
MQTT:     localhost:1883
```

Logs anzeigen:

```bash
docker compose logs -f
```

Stoppen:

```bash
docker compose stop
```

Container entfernen, persistente Docker-Volumes aber behalten:

```bash
docker compose down
```

Achtung: `docker compose down -v` löscht auch die persistenten Daten.

## Node-RED-Flow nutzen

Der exportierte Flow liegt unter:

```text
nodered/flows.json
```

Falls der Flow nach dem ersten Start nicht automatisch in Node-RED erscheint, importiere ihn manuell über:

```text
Node-RED → Menü → Import → nodered/flows.json
```

Der Flow macht im Kern zwei Dinge:

1. Shelly-MQTT-Nachrichten empfangen, bereinigen und in das InfluxDB-Measurement `shelly_plug` schreiben.
2. Optional CO₂-Intensitätsdaten von Electricity Maps abrufen und in `grid_carbon_intensity` schreiben.

Nach dem Import solltest du die InfluxDB-Nodes in Node-RED prüfen und sicherstellen, dass URL, Organisation, Bucket und Token zu deiner `.env` passen.

## Shelly-Steckdosen einrichten

Die Shelly-Geräte müssen im selben Netzwerk erreichbar sein und MQTT an diesen Broker senden:

```text
<HOST-IP>:1883
```

Als MQTT-Präfix sollte ein stabiler Gerätename verwendet werden, zum Beispiel:

```text
orchestrator
pc
rpi5-8gb
rpi5-16gb
oldlaptop
```

Node-RED nutzt dieses Präfix als Geräte-Tag in InfluxDB. Dadurch können Messwerte später pro Gerät gefiltert und mit Experimentläufen des Orchestrators verknüpft werden.

## Grafana und InfluxDB

Grafana bekommt die InfluxDB-Datenquelle über diese Datei provisioniert:

```text
grafana/provisioning/datasources/influxdb.yml
```

Dashboards können in Grafana erstellt oder importiert werden. Exportiere fertige Dashboards als JSON, wenn sie versioniert oder in einer Abgabe nachvollziehbar dokumentiert werden sollen.

### Grafana-Dashboards

Die Grafana-Dashboards werden versioniert im Repository abgelegt und beim Start von Grafana automatisch provisioniert. Dafür liegen die Dashboard-Exporte im Ordner `grafana/dashboards/` und die Provisioning-Konfiguration unter `grafana/provisioning/dashboards/dashboards.yml`.



## Verbindung zum GreenAI-Orchestrator

Der Orchestrator schreibt Trainings-, Inferenz- und Energieauswertungen in diese InfluxDB. Aus der Orchestrator-VM darf dafür nicht `http://influxdb:8086` verwendet werden, weil dieser Name nur innerhalb des Docker-Compose-Netzwerks gilt.

Nutze stattdessen die vom Orchestrator erreichbare Host-Adresse:

```env
INFLUX_URL=http://<HOST-IP>:8086
INFLUX_ORG=thade
INFLUX_BUCKET=greenaidata
INFLUX_TOKEN=<INFLUXDB_ADMIN_TOKEN>
```

Diese Werte gehören in die lokale Influx-Konfiguration des Orchestrators, zum Beispiel in `.env.influx`. Tokens und Passwörter nicht in Git versionieren.

## Electricity Maps

Der Node-RED-Flow enthält eine optionale Abfrage der Electricity-Maps-API. Dafür müssen gesetzt sein:

```env
ELECTRICITY_MAPS_TOKEN=<token>
ELECTRICITY_MAPS_ZONE=DE
```

Der entsprechende Inject-Knoten ist für die Demonstration deaktiviert. Aktiviere ihn nur, wenn ein gültiger API-Token vorhanden ist und die InfluxDB-Zielkonfiguration geprüft wurde.

## Sicherheit

Die Mosquitto-Demokonfiguration erlaubt anonyme MQTT-Verbindungen. Das ist für ein isoliertes lokales Testnetz einfach, sollte aber nicht öffentlich erreichbar betrieben werden.

Für einen abgesicherten Betrieb:

- `allow_anonymous false` in `mosquitto/config/mosquitto.conf` setzen,
- eine Mosquitto-Passwortdatei verwenden,
- Ports nicht unnötig ins öffentliche Netzwerk freigeben,
- `.env`, Tokens, Passwörter, Datenbank-Volumes und Backups nicht in Git speichern.

## Typische Fehler

**Keine Daten in Grafana:** Prüfe zuerst, ob Shelly → MQTT → Node-RED → InfluxDB funktioniert. In Node-RED helfen Debug-Nodes und die Container-Logs.

**Orchestrator erreicht InfluxDB nicht:** Verwende aus der VM die Host-IP des Docker-Systems, nicht den internen Compose-Namen `influxdb`.

**Node-RED-Flow schreibt nicht:** Prüfe die InfluxDB-Konfiguration der Nodes sowie Bucket, Organisation und Token.

**Daten nach Neustart weg:** Prüfe, ob versehentlich `docker compose down -v` verwendet wurde.
