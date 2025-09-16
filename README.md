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
  - data: table.image_front_small_url
    name: Bild
    modify: |
      x ? `<img src="${x}" style="height: 80px; border-radius: 4px;">` : ''

```
<img width="1351" height="472" alt="image" src="https://github.com/user-attachments/assets/7266f4a6-5da3-4d7a-8e36-253b49a33d4a" />



