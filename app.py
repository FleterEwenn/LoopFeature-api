from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import loopfeature
from pathlib import Path
import uuid
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

app = Flask(__name__)
CORS(app)

storage_dir = Path(__file__).parent / "storage"
storage_dir.mkdir(exist_ok=True)

def delete_expired_gpx():
    for gpx_file in storage_dir.iterdir():
        ctime = gpx_file.stat().st_mtime
        now = time.time()

        if now - ctime >= 24*3600:
            gpx_file.unlink()
            app.logger.info("expired gpx_file succesfully deleted - path=%s", str(gpx_file))

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": "LoopFeature API"
    })

@app.route("/generate")
def generate():
    delete_expired_gpx()
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        dist = float(request.args["dist"])
        if dist <= 0:
            app.logger.exception("negative distance - dist=%s", request.args.get("dist"))
            return jsonify({"error" : "distance(dist) must be positive"}), 400
        if lat > 90 or lat < -90:
            app.logger.exception("not valide latitude - lat=%s", request.args.get("lat"))
            return jsonify({"error" : "latitude(lat) must be between -90 and 90"}), 400
        if lon > 90 or lon < -90:
            app.logger.exception("not valide longitude - lon=%s", request.args.get("lon"))
            return jsonify({"error" : "longitude(lon) must be between -90 and 90"}), 400

    except (ValueError, TypeError) as e:
        app.logger.exception("parameters conversion error - lat=%s, lon=%s, dist=%s", request.args.get("lat"), request.args.get("lon"), request.args.get("dist"))
        return jsonify({"error" : "args given are not float"}), 400
    except Exception:
        app.logger.exception("parameters error - lat=%s, lon=%s, dist=%s", request.args.get("lat"), request.args.get("lon"), request.args.get("dist"))
        return jsonify({"error" : "request takes 3 float args lat, lon and dist"}), 400
    
    try:
        list_points, total_dist = loopfeature.generate_route(lat, lon, dist)
        app.logger.info("route successfully generated - points : %s, dist : %s", len(list_points), total_dist)
    except Exception:
        app.logger.exception("generate_route error - lat=%s, lon=%s, dist=%s", lat, lon, dist)
        return jsonify({"error" : "internal server error : generate_route"}), 500
    
    dict_response = {"route": []}
    for point in list_points:
        pt_fordict = {
            "lat" : point.latitude,
            "lon" : point.longitude,
            "elev" : point.elevation
        }
        dict_response["route"].append(pt_fordict)

    gpxfile_id = str(uuid.uuid4())

    try:
        loopfeature.save_gpx(list_points, gpxfile_id, str(storage_dir))
        app.logger.info("gpx file successfully saved - gpx_id=%s, storage_dir=%s", gpxfile_id, str(storage_dir))
    except Exception:
        app.logger.exception("cannot save gpx file - gpx_id=%s, storage_dir=%s", gpxfile_id, str(storage_dir))
        return jsonify({"error" : f"cannot save gpx file"}), 500

    dict_response["id"] = gpxfile_id

    return jsonify(dict_response)

@app.route("/getgpx/<id>")
def getgpx(id):
    delete_expired_gpx()
    file = storage_dir / f"{id}.gpx"
    if not file.exists():
        app.logger.warning("gpx file not found : %s", file)
        return jsonify({"error" : f"{id} file was not found"}), 404
    
    response = send_file(file, mimetype="application/gpx+xml")

    @response.call_on_close
    def removegpx():
        try:
            file.unlink()
            app.logger.info("downloaded gpx file successfully deleted - file=%s", file)
        except Exception:
            app.logger.exception("cannot remove gpx file : %s", file)

    return response
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)