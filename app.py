# app.py
from flask import Flask, render_template, request,Response, jsonify,redirect, stream_with_context
import ee
from code2 import run_forest_model
from timeseries import get_yearly_timeseries, get_monthly_timeseries, get_seasonal_timeseries
from code4 import get_ndvi_evi_timeseries
from code3 import export_ndvi_png, export_geotiff
from code6 import get_classified_forest_map
from code5 import get_prediction_map
import traceback
import os
import requests


app = Flask(__name__)
# ee.Initialize(project='hirkanyforest')
project_id = os.environ.get("EE_PROJECT_ID", "hirkanyforest")
service_account = os.environ.get("EE_SERVICE_ACCOUNT")
private_key_json = os.environ.get("EE_PRIVATE_KEY_JSON")

if service_account and private_key_json:
    credentials = ee.ServiceAccountCredentials(
        service_account,
        key_data=private_key_json
    )
    ee.Initialize(credentials, project=project_id)
else:
    ee.Initialize(project=project_id)

@app.route("/ping")
def ping():
    return jsonify({"status":"ok"})

# @app.route("/ping")
# def ping():
#     return{"status":"ok"}

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/indicators")
def analysis():
    return render_template("stage2.html")


@app.route("/api/indices")
def get_indices():
    try:
        target_index = request.args.get("index")
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")

        if not all([target_index, start_date, end_date]):
            return jsonify({
                "success": False,
                "message": "پارامترهای ارسالی (شاخص یا تاریخ) ناقص است"
            })
        indices_dict = run_forest_model(start_date, end_date)

        if indices_dict is None or target_index not in indices_dict:
            return jsonify({
                "success": False,
                "message": "تصویری برای این بازه یا این شاخص یافت نشد"
            })
        selected_image = indices_dict[target_index]

        geometry = ee.Geometry.Rectangle([48.87, 38.30, 48.88, 38.31])
        stats = selected_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=20,
            maxPixels=1e8
        )
        value = stats.get(target_index).getInfo()

        if value is None:
            return jsonify({
                "success": False,
                "message": f"داده {target_index} برای این بازه قابل محاسبه نیست"
            })
        return jsonify({
            "success": True,
            "value": value,
            "indexName": target_index
        })

    except ee.ee_exception.EEException as e:
        return jsonify({
            "success": False,
            "message": f"خطای Earth Engine: {str(e)}"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": "خطای غیرمنتظره در پردازش داده‌ها",
            "details": str(e)
        })


@app.route("/api/timeseries")
def timeseries():
    mode = request.args.get("mode", "yearly")
    try:
        if mode == "monthly":
            data = get_monthly_timeseries(2025)
        elif mode == "seasonal":
            data = get_seasonal_timeseries(2025)
        elif mode == "yearly":
            data = get_yearly_timeseries()
        else:
            return jsonify({"success": False, "error": "Invalid mode"}), 400
        return jsonify({"success": True, "data": data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/api/classified-map")
def classified_map():
    data = get_classified_forest_map()

    return jsonify({
        "success": True,
        "tileUrl": data["tileUrl"]
    })


@app.route("/api/timeseries-v4")
def timeseries_v4():
    mode = request.args.get("mode", "monthly")
    data = get_ndvi_evi_timeseries(mode)
    return jsonify({
        "success": True,
        "data": data
    })

def fetch_earth_engine_file(url, content_type, filename):
    response = requests.get(
        url,
        stream=True,
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    if response.status_code != 200:
        return jsonify({
            "success": False,
            "error": f"Earth Engine download failed: {response.status_code}",
            "details": response.text[:500]
        }), response.status_code

    return Response(
        stream_with_context(response.iter_content(chunk_size=8192)),
        content_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.route("/api/download/geotiff")
def download_geotiff():
    try:
        url = export_geotiff()
        return stream_earth_engine_file(
            url,
            "image/tiff",
            "hyrcanian_ndvi.tif"
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/download/geotiff")
def download_geotiff():
    try:
        url = export_geotiff()
        return stream_earth_engine_file(
            url,
            "image/tiff",
            "hyrcanian_ndvi.tif"
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/prediction-map")
def prediction_map():
    data = get_prediction_map()
    return jsonify({
        "success": True,
        "tileUrl": data["tileUrl"]
    })


if __name__ == "__main__":
    print("Flask server starting...")
    app.run(host="0.0.0.0", port=5000, debug=True)
