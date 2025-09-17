# Speisekammer_HomeAssistant
Custom Integration Speisekammer 

SwaggerAPI Doku unter https://app.speisekammer.app/developer

1. Eingabe des Token
   <img width="408" height="302" alt="image" src="https://github.com/user-attachments/assets/13aa4413-4068-4e18-bc2f-17371af3387a" />
2. Auflistung der vorhanden Communities
   <img width="457" height="333" alt="image" src="https://github.com/user-attachments/assets/27e4c6af-b546-4933-a0d1-5a9e477f57d7" />
3. Bestätigen und fertig
4. Es wird für jeden Lagerort ein Sensor angelegt
5. Artikelliste als custom-table-flex Card (auch mehrere Möglich)

```yaml
type: custom:flex-table-card
title: Artikelübersicht
enable_search: true
selectable: true
sort_by: table.Name
entities:
  - sensor.lagerplatz_1_1
  - sensor.lagerplatz_1_2
  - sensor.lagerplatz_1_3
  - sensor.lagerplatz_1_4
  - sensor.lagerplatz_2_1
  - sensor.lagerplatz_2_2
  - sensor.lagerplatz_2_3
  - sensor.lagerplatz_2_4
  - sensor.lagerplatz_2_5
columns:
  - data: table.Name
    name: Artikel
    modify: |
      x ? `<div style="overflow-wrap: anywhere;">${x}</div>` : ''
  - data: table.Menge
    name: Menge
  - data: table.GTIN
    name: GTIN
    modify: |
      x ? `<div style="overflow-wrap: anywhere;">${x}</div>` : ''
  - data: table.Ablaufdatum
    name: Ablaufdatum
    modify: >
      x ? `<div style="overflow-wrap: anywhere;">${new
      Date(x).toLocaleDateString('de-DE')}</div>` : '–'
  - data: table.Lagerplatz
    name: Lagerplatz
    modify: |
      x ? `<div style="overflow-wrap: anywhere;">${x}</div>` : ''
  - data: table.Bild
    name: Bild
    modify: |
      x ? `<img src="${x}" style="height: 80px; border-radius: 4px;">` : ''

```
<img width="1351" height="472" alt="image" src="https://github.com/user-attachments/assets/7266f4a6-5da3-4d7a-8e36-253b49a33d4a" />
--------------------
In Entwicklung
<img width="923" height="689" alt="image" src="https://github.com/user-attachments/assets/61a190ea-edac-4044-a260-f71d16eb94b9" />

Artikel hinzufügen
1. Helfer anlegen
```YAML
input_text:
  gtin_eingabe:
    name: GTIN Eingabe
    max: 13

input_number:
  menge_eingabe:
    name: Menge
    min: 1
    max: 100
    step: 1

input_datetime:
  mhd_eingabe:
    name: Mindesthaltbarkeitsdatum
    has_date: true
    has_time: false

input_select:
  lagerort_auswahl:
    name: Lagerort
    options:
      - Bitte wählen
    initial: Bitte wählen

```
2. Skript
```YAML
alias: Artikel erfassen
sequence:
  - data:
      gtin: "{{ states('input_text.gtin_eingabe') }}"
      count: "{{ states('input_number.menge_eingabe') | int }}"
      best_before: "{{ states('input_datetime.mhd_eingabe') }}"
      location_name: "{{ states('input_select.lagerort_auswahl') }}"
    action: speisekammer.add_item
```
```YAML
alias: Lagerort prüfen
sequence:
  - data:
      gtin: "{{ states('input_text.gtin_eingabe') }}"
    action: speisekammer.get_locations_for_gtin
mode: single
```
4. Lovelance Dashboard Artikelerfassung
```YAML
title: Speisekammer Artikelerfassung
type: vertical-stack
cards:
  - type: entities
    title: Artikel-Daten eingeben
    entities:
      - entity: input_text.gtin_eingabe
        name: GTIN
      - entity: sensor.speisekammer_artikelabfrage
        name: Artikelname
      - entity: input_number.menge_eingabe
        name: Menge
      - entity: input_datetime.mhd_eingabe
        name: MHD
      - entity: input_select.lagerort_auswahl
        name: Lagerort
  - type: horizontal-stack
    cards:
      - show_name: true
        show_icon: true
        type: button
        name: Artikel laden
        icon: mdi:database-search
        tap_action:
          action: call-service
          service: script.lagerort_prufen
      - show_name: true
        show_icon: true
        type: button
        name: Artikel ändern
        icon: mdi:package-variant
        tap_action:
          action: call-service
          service: script.artikel_erfassen
  - type: sensor
    entity: sensor.speisekammer_artikelabfrage
    name: Artikelvorschau
```
-----------------------------
**INVENTUR Modus aktuell noch nicht funktionsfähig**

start_inventur → Inventur wird gestartet, aktuelle Artikel aus dem Lager werden geladen, Sensor auf „Running“ gesetzt.

scan_article → Für jeden gescannten Artikel: GTIN eingeben, Menge ggf. anpassen, Service ausführen → die Inventur-Daten (ist-Werte) werden aktualisiert.

Flex-Table Sensor (InventurSensor) → zeigt laufend aktualisierte Tabelle mit allen gescannten Artikeln, Mengen, Soll/Ist, Lagerort und MHD. Die Tabelle aktualisiert sich nach jedem scan_article.

stop_inventur → beendet die Inventur, schreibt alle Änderungen zurück ins Lager (update_stock), Sensor wird wieder auf „Idle“ gesetzt.

Helfer anlegen
```YAML
input_boolean:
  inventurmodus:
    name: Inventurmodus
    icon: mdi:clipboard-list
    initial: off
```
Skript anlegen
```YAML
alias: Start Inventur mit Lagerortprüfung
description: Prüft den Lagerort anhand der GTIN und startet dann die Inventur
mode: single
sequence:
  - data:
      gtin: "{{ states('input_text.gtin_eingabe') }}"
    action: speisekammer.get_locations_for_gtin
  - delay:
      seconds: 1
  - data: {}
    action: speisekammer.start_inventur
```
Dashboard anlegen
```YAML
type: entities
title: Speisekammer Inventur
entities:
  - entity: input_boolean.inventurmodus
    name: Inventurmodus aktiv
  - entity: sensor.speisekammer_inventur
    name: Status
    attribute: table_data
```
```YAML
type: horizontal-stack
cards:
  - show_name: true
    show_icon: true
    type: button
    name: Start Inventur
    icon: mdi:play
    tap_action:
      action: perform-action
      perform_action: script.start_inventur_mit_lagerortprufung
      target: {}
    show_state: false
  - type: button
    name: Scan Artikel
    icon: mdi:barcode-scan
    show_name: true
    show_icon: true
    show_state: false
    tap_action:
      action: call-service
      service: speisekammer.scan_article
      service_data:
        gtin: "{{ states('input_text.gtin_eingabe') }}"
        count: "{{ states('input_number.menge_eingabe') | int }}"
        mhd: "{{ states('input_datetime.mhd_eingabe') }}"
        entry_id: >-
          {{ state_attr('sensor.speisekammer_inventur', 'entry_id') |
          default('default') }}
  - type: button
    name: Stop Inventur
    icon: mdi:stop
    show_name: true
    show_icon: true
    show_state: false
    tap_action:
      action: call-service
      service: speisekammer.stop_inventur
      service_data:
        entry_id: >-
          {{ state_attr('sensor.speisekammer_inventur', 'entry_id') |
          default('default') }}
```
```YAML
type: entities
title: Artikel scannen
show_header_toggle: false
entities:
  - entity: input_text.gtin_eingabe
    name: Artikel GTIN
  - entity: input_number.menge_eingabe
    name: Menge
  - entity: input_datetime.mhd_eingabe
    name: MHD
  - entity: input_select.lagerort_auswahl
    name: Lagerort
```
```YAML
type: custom:flex-table-card
title: Inventur Übersicht
entities:
  - entity: sensor.speisekammer_inventur
columns:
  - data: table_data.Name
    name: Artikel
  - data: table_data.Barcode
    name: Barcode
  - data: table_data.Menge_SOLL
    name: Menge SOLL
  - data: table_data.Menge_IST
    name: Menge IST
  - data: table_data.Lager
    name: Lager
  - data: table_data.MHD
    name: MHD

```

