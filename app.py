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
    except ValueError or TypeError:
        return jsonify({"error" : "args given are not float"}), 400
    except:
        return jsonify({"error" : "request takes 3 float args lat, lon and dist"}), 400
    
    try:
        list_points, total_dist = loopfeature.generate_route(lat, lon, dist)
    except:
        return jsonify({"error" : "generate_route return an error"}), 400
    
    dict_response = {"route": []}
    for point in list_points:
        pt_fordict = {
            "lat" : point.latitude,
            "lon" : point.longitude,
            "elev" : point.elevation
        }
        dict_response["route"].append(pt_fordict)

    gpxfile_id = str(uuid.uuid4())

    loopfeature.save_gpx(list_points, gpxfile_id, str(storage_dir))

    dict_response["id"] = gpxfile_id

    return jsonify(dict_response)

@app.route("/getgpx/<id>")
def getgpx(id):
    file = storage_dir / f"{str(id)}.gpx"
    if not file.exists():
        return jsonify({"error" : f"{id} file was not found"}), 404
    
    response = send_file(file, mimetype="application/gpx+xml")

    @response.call_on_close
    def removegpx():
        file.unlink()

    return response
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)