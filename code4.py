import ee
import datetime

def get_ndvi_evi_timeseries(mode="monthly", year=2025):
    roi = ee.Geometry.Rectangle([48.87, 38.30, 48.88, 38.31])

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .filterDate(f"{year}-01-01", f"{year}-12-31")
    )

    def add_indices(image):
        nir = image.select("B8")
        red = image.select("B4")
        blue = image.select("B2")

        ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
        evi = image.expression(
            "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
            {"NIR": nir, "RED": red, "BLUE": blue}
        ).rename("EVI")

        return image.addBands([ndvi, evi])

    collection = collection.map(add_indices)

    labels, ndvi_values, evi_values = [], [], []

    if mode == "monthly":
        for m in range(1, 13):
            start = ee.Date.fromYMD(year, m, 1)
            end = start.advance(1, "month")

            img = collection.filterDate(start, end).mean()

            stats = img.reduceRegion(
                ee.Reducer.mean(),
                roi,
                scale=20,
                maxPixels=1e8
            )

            labels.append(f"{m}")
            ndvi_values.append(stats.get("NDVI").getInfo())
            evi_values.append(stats.get("EVI").getInfo())

    elif mode == "seasonal":
        seasons = {
            "بهار": (3, 6),
            "تابستان": (6, 9),
            "پاییز": (9, 12),
            "زمستان": (12, 3)
        }

        for name, (start_m, end_m) in seasons.items():
            start = ee.Date.fromYMD(year, start_m, 1)
            end = ee.Date.fromYMD(year if end_m != 3 else year + 1, end_m, 1)

            img = collection.filterDate(start, end).mean()

            stats = img.reduceRegion(
                ee.Reducer.mean(),
                roi,
                scale=20,
                maxPixels=1e8
            )

            labels.append(name)
            ndvi_values.append(stats.get("NDVI").getInfo())
            evi_values.append(stats.get("EVI").getInfo())

    return {
        "labels": labels,
        "ndvi": ndvi_values,
        "evi": evi_values
    }
