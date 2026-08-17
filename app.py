import os
import phonenumbers
from phonenumbers import carrier, geocoder
from opencage.geocoder import OpenCageGeocoder
from flask import Flask, render_template, request, jsonify
import folium

app = Flask(__name__)

# Metti la tua chiave OpenCage come variabile d'ambiente su Render
# (Settings -> Environment -> Add Environment Variable -> OPENCAGE_KEY)
OPENCAGE_KEY = os.environ.get("OPENCAGE_KEY", "")


@app.route("/")
def index():
    return render_template("index.html")


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
