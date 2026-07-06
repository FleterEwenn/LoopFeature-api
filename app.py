from flask import Flask, request, jsonify, send_file
import loopfeature
from pathlib import Path
import uuid
import os

app = Flask(__name__)
storage_dir = Path(__file__).parent / "storage"

@app.route("/")
def home():
    return jsonify({
        "name" : "LoopFeature-API"
    })

@app.route("/generate")
def generate():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        dist = float(request.args["dist"])
    except ValueError:
        return jsonify({"error" : "args given are not float"}), 400
    except:
        return jsonify({"error" : "request takes 3 float args lat, lon and dist"}), 400
    
    try:
        list_points, total_dist = loopfeature.generate_route(lat, lon, dist)
    except:
        return jsonify({"error" : "generate_route return an error"}), 500
    
    dict_response = {"route": []}
    for point in list_points:
        pt_fordict = {
            "lat" : point.latitude,
            "lon" : point.longitude,
            "elev" : point.elevation
        }
        dict_response["route"].append(pt_fordict)

    gpxfile_id = str(uuid.uuid4())
    filename = gpxfile_id + ".gpx"
    while os.path.exists(storage_dir / filename):
        gpxfile_id = str(uuid.uuid4())
        filename = gpxfile_id + ".gpx"

    loopfeature.save_gpx(list_points, gpxfile_id, str(storage_dir))

    dict_response["id"] = gpxfile_id

    return jsonify(dict_response)

@app.route("/getgpx/<id>")
def getgpx(id):
    file = str(id) + ".gpx"
    if os.path.exists(storage_dir / file):
        return send_file(storage_dir / file)
    else:
        return jsonify({"error" : f"{id} file was not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)