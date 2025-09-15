# Speisekammer_HomeAssistant
Custom Integration Speisekammer 

SwaggerAPI Doku unter https://app.speisekammer.app/developer

1. Eingabe des Token <img width="421" height="293" alt="image" src="https://github.com/user-attachments/assets/9e61e3e8-5e80-4ca8-89cd-85d6491e2e93" />

3. Auflistung der vorhanden Communities <img width="457" height="333" alt="image" src="https://github.com/user-attachments/assets/27e4c6af-b546-4933-a0d1-5a9e477f57d7" />

4. Bestätigen und fertig
5. Es stehen aktuell drei Übersichtsentitäten zur Verfügung
   <img width="1197" height="192" alt="image" src="https://github.com/user-attachments/assets/50e234a3-2e60-40a8-9fb0-8087765dc031" />
6. Zusätzlich noch für jeden Lagerort eine extra Entität / Sensor
<img width="549" height="612" alt="image" src="https://github.com/user-attachments/assets/7f99f02a-5758-4667-8f87-78c0acd6232b" />


Zum Ändern und Aktualisieren der Daten muss in der configuration.yaml folgendes hinzugefügt werden
input_text:
  sk_gtin:
    name: GTIN
    initial: ""
  sk_description:
    name: Beschreibung
    initial: ""
  sk_community_id:
    name: Community-ID
    initial: "DEINE_COMMUNITY_ID"

input_number:
  sk_count:
    name: Anzahl
    min: 0
    max: 100
    step: 1

input_datetime:
  sk_best_before:
    name: MHD
    has_date: true
    has_time: false
