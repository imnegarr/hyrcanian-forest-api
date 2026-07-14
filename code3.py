import ee


def export_ndvi_png():
    roi = ee.Geometry.Rectangle([48.5, 36.8, 50.5, 38.8])

    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate("2025-10-01", "2026-01-31")
        .median()
        .clip(roi)
    )

    ndvi = image.normalizedDifference(["B8", "B4"])

    return ndvi.visualize(
        min=-0.2,
        max=0.8,
        palette=["#c0392b", "#f1c40f", "#27ae60"]
    ).getThumbURL({
        "region": roi,
        "dimensions": 1000,
        "format": "png"
    })


def export_geotiff():
    roi = ee.Geometry.Rectangle([49.0, 37.0, 50.0, 38.0])

    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate("2025-10-01", "2026-01-31")
        .median()
        .clip(roi)
    )

    ndvi = image.normalizedDifference(["B8", "B4"])

    return ndvi.getDownloadURL({
        "scale": 60,
        "region": roi,
        "fileFormat": "GeoTIFF"
    })
