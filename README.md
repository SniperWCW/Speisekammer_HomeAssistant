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
title: Lagerplatz 1-1
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
  - data: table.Menge
    name: Menge
  - data: table.GTIN
    name: GTIN
  - data: table.Ablaufdatum
    name: Ablaufdatum
    modify: |
      x ? (new Date(x).toLocaleDateString('de-DE')) : '–'
  - data: table.Lagerplatz
    name: Lagerplatz
```
<img width="1314" height="246" alt="image" src="https://github.com/user-attachments/assets/72431329-1061-46c7-90ee-b9fd64ddcc03" />


