from flask import Flask, request, jsonify
from loopfeature import generate_route, save_gpx
from pathlib import Path
import uuid

app = Flask(__name__)
storage_dir = Path(__file__).parent / "storage"

@app.route("/generate")
def generate():
    lat = float(request.args["lat"])
    lon = float(request.args["lon"])
    dist = float(request.args["dist"])

    list_points, total_dist = generate_route(lat, lon, dist)

    dict_response = {"route": []}
    for point in list_points:
        pt_fordict = {
            "lat" : point.latitude,
            "lon" : point.longitude,
            "elev" : point.elevation
        }
        dict_response["route"].append(pt_fordict)
    
    gpxfile_id = str(uuid.uuid4())
    save_gpx(list_points, gpxfile_id, str(storage_dir))

    dict_response["id"] = gpxfile_id

    return jsonify(dict_response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)