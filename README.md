# GreenAI Sustainability Architecture

Dieses Repository enthält die Docker-Compose-basierte Nachhaltigkeitsarchitektur der GreenAI-Demonstrationsumgebung.

Die Architektur sammelt, verarbeitet und visualisiert Energie- und CO₂-bezogene Messdaten. Sie läuft außerhalb der GreenAI-Orchestrator-VM und stellt zentrale Dienste bereit, auf die der GreenAI-Orchestrator schreiben bzw. zugreifen kann.

## Zweck

Die Nachhaltigkeitsarchitektur dient dazu,

- Sensordaten, insbesondere Shelly-/MQTT-Messwerte, über Mosquitto entgegenzunehmen,
- Messwerte in Node-RED zu transformieren,
- Energie- und CO₂-Metriken in InfluxDB zu speichern,
- Dashboards und Datenquellen über Grafana bereitzustellen,
- externe CO₂-Intensitätsdaten über die Electricity-Maps-API einzubinden.

Die GreenAI-Orchestrator-VM nutzt diese externe Infrastruktur, um Experimentmetriken und Energie-/CO₂-Daten in InfluxDB zu schreiben.

## Architekturüberblick

Die Umgebung besteht aus vier Docker-Services:

| Service | Zweck | Port |
|---|---|---|
| Mosquitto | MQTT-Broker für IoT-/Shelly-Messwerte | `1883` |
| InfluxDB 2.x | Zeitreihendatenbank für Energie-, CO₂- und Experimentdaten | `8086` |
| Node-RED | Datenflusslogik für MQTT, Transformation und externe API-Abfragen | `1880` |
| Grafana | Visualisierung der Mess- und Nachhaltigkeitsdaten | `3000` |

Interne Kommunikation innerhalb des Docker-Compose-Netzwerks erfolgt über die Servicenamen:

```text
mosquitto
influxdb
nodered
grafana
```

Beispiele:

```text
http://influxdb:8086
mqtt://mosquitto:1883
```

Von außerhalb der Docker-Compose-Umgebung, z. B. aus der GreenAI-Orchestrator-VM, muss die InfluxDB über die Host-IP oder den Hostnamen des Windows-Systems erreicht werden, z. B.:

```text
http://<HOST-IP>:8086
```

## Repository-Inhalt

```text
green-ai-sustainability/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── influxdb.yml
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
└── nodered/
    └── flows.json
```

## Nicht im Repository enthalten

Aus Sicherheits- und Größen-Gründen sind folgende Dateien und Daten absichtlich nicht im Git-Repository enthalten:

```text
.env
Mosquitto-Passwortdateien, z. B. mosquitto/config/passwd
Docker-Volumes
InfluxDB-Datenbankdaten
Grafana-Datenbankdaten
Node-RED Runtime-Daten
Mosquitto Runtime-Daten und Logs
API-Tokens
Passwörter
private Schlüssel
Backup-Archive
```

Die Datei `.env.example` enthält nur Platzhalter. Für den produktiven Betrieb muss daraus lokal eine `.env` erstellt werden.

## Voraussetzungen

Benötigt werden:

- Windows-System mit Docker Desktop
- Docker Compose
- Zugriff auf die benötigten Ports:
  - `1883` für MQTT
  - `1880` für Node-RED
  - `3000` für Grafana
  - `8086` für InfluxDB

Optional:

- Electricity-Maps-API-Token für CO₂-Intensitätsdaten
- GreenAI-Orchestrator-VM, die in diese InfluxDB schreibt

## Schnellstart

Repository klonen:

```powershell
git clone https://gitup.uni-potsdam.de/egenhoff/green-ai-sustainability.git
cd green-ai-sustainability
```

Beispielkonfiguration kopieren:

```powershell
Copy-Item .env.example .env
notepad .env
```

In `.env` müssen die Platzhalter durch lokale Werte ersetzt werden.

Beispiel:

```env
TZ=Europe/Berlin

MQTT_USER=greenai
MQTT_PASSWORD=set_your_own_password

INFLUXDB_USERNAME=admin
INFLUXDB_PASSWORD=set_your_own_password
INFLUXDB_ORG=thade
INFLUXDB_BUCKET=greenaidata
INFLUXDB_ADMIN_TOKEN=INSERT_TOKEN

GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=set_your_own_password

ELECTRICITY_MAPS_TOKEN=INSERT_TOKEN
ELECTRICITY_MAPS_ZONE=DE
```

Container starten:

```powershell
docker compose up -d
```

Status prüfen:

```powershell
docker compose ps
```

Logs anzeigen:

```powershell
docker compose logs -f
```

Container stoppen:

```powershell
docker compose stop
```

Container stoppen und entfernen, Volumes aber behalten:

```powershell
docker compose down
```

Achtung: Dieser Befehl löscht Volumes und damit persistente Daten:

```powershell
docker compose down -v
```

Nur verwenden, wenn die Daten bewusst gelöscht werden sollen.

## Dienste aufrufen

Nach dem Start sind die Dienste lokal erreichbar:

```text
Grafana:   http://localhost:3000
InfluxDB:  http://localhost:8086
Node-RED:  http://localhost:1880
Mosquitto: localhost:1883
```

## InfluxDB

InfluxDB wird beim ersten Start über die Variablen aus `.env` initialisiert:

```env
INFLUXDB_USERNAME
INFLUXDB_PASSWORD
INFLUXDB_ORG
INFLUXDB_BUCKET
INFLUXDB_ADMIN_TOKEN
```

Die Daten werden persistent im Docker Named Volume gespeichert:

```text
iot-monitoring_influxdb_data
```

Die Konfiguration wird gespeichert in:

```text
iot-monitoring_influxdb_config
```

Innerhalb des Docker-Netzwerks ist InfluxDB erreichbar unter:

```text
http://influxdb:8086
```

Von der GreenAI-Orchestrator-VM aus muss stattdessen die IP-Adresse oder der Hostname des Windows-Systems verwendet werden, z. B.:

```text
http://<WINDOWS-HOST-IP>:8086
```

Die entsprechende Konfiguration liegt im Orchestrator-Projekt typischerweise in:

```text
.env.influx
```

## Grafana

Grafana wird über Docker Compose gestartet und nutzt folgende Umgebungsvariablen:

```env
GRAFANA_ADMIN_USER
GRAFANA_ADMIN_PASSWORD
INFLUXDB_ORG
INFLUXDB_BUCKET
INFLUXDB_ADMIN_TOKEN
```

Die InfluxDB-Datenquelle wird über diese Datei provisioniert:

```text
grafana/provisioning/datasources/influxdb.yml
```

Grafana speichert lokale Zustände, Dashboards und Einstellungen zusätzlich im Docker Named Volume:

```text
iot-monitoring_grafana_data
```

Falls Dashboards über die Grafana-Oberfläche erstellt oder verändert werden, sollten sie zusätzlich als JSON exportiert und versioniert werden, damit sie unabhängig vom Volume nachvollziehbar bleiben.

## Node-RED

Node-RED läuft auf Port `1880`.

Der exportierte Flow liegt im Repository unter:

```text
nodered/flows.json
```

Der Flow enthält unter anderem:

- MQTT-Eingang für Sensordaten,
- Transformation von Shelly-Messwerten,
- Schreiben von Messwerten nach InfluxDB,
- Abfrage der aktuellen CO₂-Intensität über Electricity Maps,
- Schreiben der CO₂-Daten in InfluxDB.

Die Node-RED-Laufzeitdaten werden im Docker Named Volume gespeichert:

```text
iot-monitoring_node_red_data
```

Der Electricity-Maps-Token wird nicht im Flow gespeichert, sondern über die Umgebungsvariable bereitgestellt:

```env
ELECTRICITY_MAPS_TOKEN
```

Die Zone wird über diese Variable gesetzt:

```env
ELECTRICITY_MAPS_ZONE
```

Beispiel:

```env
ELECTRICITY_MAPS_ZONE=DE
```

## Mosquitto

Mosquitto dient als MQTT-Broker für IoT-/Shelly-Messwerte.

Die Konfiguration liegt unter:

```text
mosquitto/config/mosquitto.conf
```

Aktueller Stand der Konfiguration:

```text
listener 1883 0.0.0.0
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
```

Damit sind anonyme MQTT-Verbindungen erlaubt. Das kann für lokale Tests praktisch sein, sollte aber für produktive oder öffentlich erreichbare Umgebungen deaktiviert werden.

Für einen abgesicherten Betrieb sollte die Konfiguration z. B. auf Passwortauthentifizierung umgestellt werden:

```text
listener 1883 0.0.0.0
allow_anonymous false
password_file /mosquitto/config/passwd
persistence true
persistence_location /mosquitto/data/
log_dest stdout
```

Die Passwortdatei `mosquitto/config/passwd` enthält Hashes und darf nicht in Git versioniert werden.

Beispiel zum Erzeugen einer Mosquitto-Passwortdatei:

```powershell
docker run --rm -it `
  -v "C:\iot-monitoring\mosquitto\config:/mosquitto/config" `
  eclipse-mosquitto:2 `
  mosquitto_passwd -c /mosquitto/config/passwd greenai
```

Danach Mosquitto neu starten:

```powershell
docker compose restart mosquitto
```

Die Mosquitto-Daten und Logs liegen in den Docker Named Volumes:

```text
iot-monitoring_mosquitto_data
iot-monitoring_mosquitto_log
```

## Docker Volumes

Die persistenten Daten liegen nicht vollständig im Projektordner, sondern in Docker Named Volumes.

Aktiv verwendete Volumes:

```text
iot-monitoring_influxdb_data
iot-monitoring_influxdb_config
iot-monitoring_grafana_data
iot-monitoring_node_red_data
iot-monitoring_mosquitto_data
iot-monitoring_mosquitto_log
```

Diese Volumes sind nicht Teil des Git-Repositories und müssen separat gesichert werden.

## Backup der Volumes

Backup-Ordner erstellen:

```powershell
cd C:\iot-monitoring

$BACKUP_DIR = "C:\iot-monitoring-backup\$(Get-Date -Format yyyy-MM-dd)"
New-Item -ItemType Directory -Force -Path $BACKUP_DIR
```

Container stoppen:

```powershell
docker compose stop
```

Volumes sichern:

```powershell
docker run --rm `
  -v iot-monitoring_influxdb_data:/data `
  -v "${BACKUP_DIR}:/backup" `
  alpine `
  tar -czf /backup/influxdb_data.tar.gz -C /data .
```

```powershell
docker run --rm `
  -v iot-monitoring_influxdb_config:/data `
  -v "${BACKUP_DIR}:/backup" `
  alpine `
  tar -czf /backup/influxdb_config.tar.gz -C /data .
```

```powershell
docker run --rm `
  -v iot-monitoring_grafana_data:/data `
  -v "${BACKUP_DIR}:/backup" `
  alpine `
  tar -czf /backup/grafana_data.tar.gz -C /data .
```

```powershell
docker run --rm `
  -v iot-monitoring_node_red_data:/data `
  -v "${BACKUP_DIR}:/backup" `
  alpine `
  tar -czf /backup/node_red_data.tar.gz -C /data .
```

```powershell
docker run --rm `
  -v iot-monitoring_mosquitto_data:/data `
  -v "${BACKUP_DIR}:/backup" `
  alpine `
  tar -czf /backup/mosquitto_data.tar.gz -C /data .
```

```powershell
docker run --rm `
  -v iot-monitoring_mosquitto_log:/data `
  -v "${BACKUP_DIR}:/backup" `
  alpine `
  tar -czf /backup/mosquitto_log.tar.gz -C /data .
```

Sensible lokale Konfigurationsdateien separat sichern:

```powershell
Copy-Item C:\iot-monitoring\.env "$BACKUP_DIR\.env"
Copy-Item C:\iot-monitoring\mosquitto\config\passwd "$BACKUP_DIR\mosquitto-passwd"
```

Falls `mosquitto/config/passwd` nicht existiert oder Mosquitto anonym betrieben wird, entfällt der zweite Befehl.

Container wieder starten:

```powershell
docker compose up -d
docker compose ps
```

Die Backup-Dateien enthalten produktive Daten und Zugangsdaten. Sie gehören nicht in GitUp und sollten nur in einem geschützten Speicher oder verschlüsselten Abgabe-Archiv abgelegt werden.

## Restore aus Volume-Backups

Vor einer Wiederherstellung sollten die Container gestoppt sein:

```powershell
cd C:\iot-monitoring
docker compose stop
```

Beispiel: InfluxDB-Datenvolume wiederherstellen:

```powershell
docker run --rm `
  -v iot-monitoring_influxdb_data:/data `
  -v C:\iot-monitoring-backup\YYYY-MM-DD:/backup `
  alpine `
  sh -c "rm -rf /data/* && tar -xzf /backup/influxdb_data.tar.gz -C /data"
```

Analog können die übrigen Volumes wiederhergestellt werden:

```text
influxdb_config.tar.gz  -> iot-monitoring_influxdb_config
grafana_data.tar.gz     -> iot-monitoring_grafana_data
node_red_data.tar.gz    -> iot-monitoring_node_red_data
mosquitto_data.tar.gz   -> iot-monitoring_mosquitto_data
mosquitto_log.tar.gz    -> iot-monitoring_mosquitto_log
```

Danach:

```powershell
docker compose up -d
docker compose ps
```

## Verbindung zur GreenAI-Orchestrator-VM

Die GreenAI-Orchestrator-VM läuft getrennt von dieser Nachhaltigkeitsarchitektur.

Innerhalb dieser Docker-Compose-Umgebung lautet die InfluxDB-Adresse:

```text
http://influxdb:8086
```

Aus der GreenAI-Orchestrator-VM muss eine von der VM erreichbare Adresse verwendet werden, z. B.:

```text
http://<WINDOWS-HOST-IP>:8086
```

Die Orchestrator-Konfiguration sollte dafür eine lokale Datei verwenden, z. B.:

```text
.env.influx
```

Beispiel:

```env
INFLUX_URL=http://<WINDOWS-HOST-IP>:8086
INFLUX_ORG=thade
INFLUX_BUCKET=greenaidata
INFLUX_TOKEN=PLEASE_SET_TOKEN_HERE
```

Diese Datei gehört nicht in Git. Im Orchestrator-Repository sollte nur eine `.env.influx.example` liegen.

## Typische Befehle

Status prüfen:

```powershell
docker compose ps
```

Logs aller Dienste anzeigen:

```powershell
docker compose logs -f
```

Logs eines Dienstes anzeigen:

```powershell
docker compose logs -f influxdb
docker compose logs -f grafana
docker compose logs -f nodered
docker compose logs -f mosquitto
```

Container neu starten:

```powershell
docker compose restart
```

Nur Node-RED neu starten:

```powershell
docker compose restart nodered
```

Nur Mosquitto neu starten:

```powershell
docker compose restart mosquitto
```

Konfiguration validieren:

```powershell
docker compose config
```

## Sicherheitshinweise

Dieses Repository ist öffentlich. Deshalb dürfen keine echten Zugangsdaten committed werden.

Nicht committen:

```text
.env
mosquitto/config/passwd
InfluxDB-Tokens
Grafana-Passwörter
Electricity-Maps-API-Token
private Schlüssel
Docker-Volume-Backups
```

Vor jedem Commit prüfen:

```powershell
git status
git diff --cached --name-only
git grep -n -i "token\|password\|secret\|api_key\|apikey\|passwd"
```

Wenn ein echter Token oder ein echtes Passwort versehentlich öffentlich committed wurde, sollte der betroffene Zugang als kompromittiert betrachtet und erneuert werden.

## Reproduzierbarkeit

Für eine reproduzierbare Neuinstallation werden benötigt:

1. Dieses Repository
2. Eine lokal erstellte `.env` auf Basis von `.env.example`
3. Optional eine Mosquitto-Passwortdatei
4. Optional die separat gesicherten Docker-Volumes
5. Zugriff auf die GreenAI-Orchestrator-VM, falls Experimente in die InfluxDB schreiben sollen

Minimalstart ohne bestehende Daten:

```powershell
git clone https://gitup.uni-potsdam.de/egenhoff/green-ai-sustainability.git
cd green-ai-sustainability
Copy-Item .env.example .env
notepad .env
docker compose up -d
```

Vollständiger Restore mit bestehendem Zustand:

```text
1. Repository klonen
2. .env aus geschütztem Backup wiederherstellen
3. Optional mosquitto/config/passwd aus geschütztem Backup wiederherstellen
4. Docker-Volumes aus separatem Backup wiederherstellen
5. docker compose up -d ausführen
```

## Hinweis zur Masterarbeit

Diese Nachhaltigkeitsarchitektur ist Teil der GreenAI-Demonstrationsumgebung. Sie dient als externe Monitoring- und Datenhaltungsschicht für Energie-, CO₂- und Experimentmetriken. Die eigentliche GreenAI-Orchestrierung läuft getrennt davon in einer virtuellen Maschine und schreibt über die konfigurierte InfluxDB-Verbindung in diese Infrastruktur.