import os
import phonenumbers
from phonenumbers import carrier, geocoder
from opencage.geocoder import OpenCageGeocoder
from flask import Flask, request, jsonify, Response
import folium

app = Flask(__name__)

# Chiave OpenCage: la metti su Render come variabile d'ambiente OPENCAGE_KEY
OPENCAGE_KEY = os.environ.get("OPENCAGE_KEY", "")

HTML_PAGE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Phone Number Tracker</title>
<style>
  body {
    background: #96BFFF;
    font-family: Arial, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30px 15px;
    margin: 0;
  }
  h1 { color: #39281E; font-size: 24px; }
  .card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    width: 100%;
    max-width: 360px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.15);
  }
  input {
    width: 100%;
    padding: 12px;
    font-size: 18px;
    text-align: center;
    border: none;
    border-radius: 8px;
    background: #2C3541;
    color: white;
    box-sizing: border-box;
    margin-bottom: 12px;
  }
  button {
    width: 100%;
    padding: 12px;
    font-size: 16px;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    background: #EE8C62;
    color: white;
    cursor: pointer;
  }
  button:active { background: #ED8051; }
  .result { margin-top: 16px; font-size: 15px; }
  .result span { font-weight: bold; }
  #map-container {
    margin-top: 16px;
    border-radius: 8px;
    overflow: hidden;
    height: 300px;
  }
  #map-container iframe { width: 100%; height: 100%; border: none; }
  .error { color: #b00020; margin-top: 10px; font-size: 14px; }
</style>
</head>
<body>

<h1>Track Number</h1>

<div class="card">
  <input type="text" id="number" placeholder="+39 123 456 7890">
  <button onclick="track()">Cerca</button>
  <div class="result" id="result" style="display:none;">
    <p>Paese: <span id="country"></span></p>
    <p>Operatore: <span id="carrier"></span></p>
  </div>
  <div id="error" class="error"></div>
  <div id="map-container"></div>
</div>

<script>
async function track() {
  const number = document.getElementById('number').value;
  const errorDiv = document.getElementById('error');
  const resultDiv = document.getElementById('result');
  const mapContainer = document.getElementById('map-container');

  errorDiv.textContent = '';
  resultDiv.style.display = 'none';
  mapContainer.innerHTML = '';

  const res = await fetch('/track', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({number})
  });
  const data = await res.json();

  if (!res.ok) {
    errorDiv.textContent = data.error;
    return;
  }

  document.getElementById('country').textContent = data.country;
  document.getElementById('carrier').textContent = data.carrier;
  resultDiv.style.display = 'block';

  if (data.map_html) {
    const iframe = document.createElement('iframe');
    iframe.srcdoc = data.map_html;
    mapContainer.appendChild(iframe);
  }
}
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return Response(HTML_PAGE, mimetype="text/html")


@app.route("/track", methods=["POST"])
def track():
    data = request.get_json()
    raw_number = data.get("number", "").strip()

    if not raw_number:
        return jsonify({"error": "Inserisci un numero di telefono."}), 400

    try:
        number = phonenumbers.parse(raw_number)
    except phonenumbers.NumberParseException:
        return jsonify({"error": "Numero non valido. Usa il formato internazionale, es. +391234567890"}), 400

    if not phonenumbers.is_valid_number(number):
        return jsonify({"error": "Numero non valido."}), 400

    location = geocoder.description_for_number(number, "it") or "Sconosciuto"
    service = carrier.name_for_number(number, "it") or "Sconosciuto"

    lat, lng = None, None
    map_html = None

    if OPENCAGE_KEY and location != "Sconosciuto":
        try:
            geo = OpenCageGeocoder(OPENCAGE_KEY)
            results = geo.geocode(location)
            if results:
                lat = results[0]["geometry"]["lat"]
                lng = results[0]["geometry"]["lng"]

                my_map = folium.Map(location=[lat, lng], zoom_start=6)
                folium.Marker([lat, lng], popup=location).add_to(my_map)
                map_html = my_map._repr_html_()
        except Exception as e:
            print("Errore OpenCage:", e)

    return jsonify({
        "country": location,
        "carrier": service,
        "lat": lat,
        "lng": lng,
        "map_html": map_html
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
