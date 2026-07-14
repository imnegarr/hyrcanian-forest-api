# timeseries.py
import ee

def compute_indices(image):
    nir = image.select("B8")
    red = image.select("B4")
    blue = image.select("B2")

    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")

    evi = image.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {"NIR": nir, "RED": red, "BLUE": blue}
    ).rename("EVI")

    savi = image.expression(
        "((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
        {"NIR": nir, "RED": red}
    ).rename("SAVI")

    dvi = nir.subtract(red).rename("DVI")

    sr = nir.divide(red).rename("SR")

    phi = ndvi.multiply(evi).rename("PHI") 

    return image.addBands([ndvi, evi, savi, dvi, sr, phi])


def get_yearly_timeseries(start_year=2018, end_year=2025):
    geometry = ee.Geometry.Rectangle([48.87, 38.30, 48.88, 38.31])

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )

    results = {
        "years": [],
        "ndvi": [],
        "evi": [],
        "savi": [],
        "dvi": [],
        "sr": [],
        "phi": []
    }

    for year in range(start_year, end_year + 1):
        start = f"{year}-01-01"
        end = f"{year}-12-31"

        yearly = (
            collection
            .filterDate(start, end)
            .map(compute_indices)
        )

        image = yearly.mean()

        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=20,
            maxPixels=1e8
        )

        values = stats.getInfo()

        results["years"].append(str(year))
        results["ndvi"].append(values.get("NDVI"))
        results["evi"].append(values.get("EVI"))
        results["savi"].append(values.get("SAVI"))
        results["dvi"].append(values.get("DVI"))
        results["sr"].append(values.get("SR"))
        results["phi"].append(values.get("PHI"))

    return results


def get_monthly_timeseries(year=2025):
    geometry = ee.Geometry.Rectangle([48.87, 38.30, 48.88, 38.31])

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .map(compute_indices)
    )

    results = {
        "labels": [],
        "ndvi": [], "evi": [], "savi": [],
        "dvi": [], "sr": [], "phi": []
    }

    for m in range(1, 13):
        start = ee.Date.fromYMD(year, m, 1)
        end = start.advance(1, "month")

        img = collection.filterDate(start, end).mean()

        stats = img.reduceRegion(
            ee.Reducer.mean(), geometry, 20, maxPixels=1e8
        ).getInfo()

        results["labels"].append(start.format("YYYY-MM").getInfo())
        for k in ["NDVI","EVI","SAVI","DVI","SR","PHI"]:
            results[k.lower()].append(stats.get(k))

    return results

def get_seasonal_timeseries(year=2025):
    seasons = [
        ("Spring", ee.Date.fromYMD(year, 3, 1), ee.Date.fromYMD(year, 6, 1)),
        ("Summer", ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 1)),
        ("Autumn", ee.Date.fromYMD(year, 9, 1), ee.Date.fromYMD(year, 12, 1)),
        ("Winter", ee.Date.fromYMD(year - 1, 12, 1), ee.Date.fromYMD(year, 3, 1))
    ]

    geometry = ee.Geometry.Rectangle([48.87, 38.30, 48.88, 38.31])

    base = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(compute_indices)
    )

    res = {
        "labels": [],
        "ndvi": [], "evi": [], "savi": [],
        "dvi": [], "sr": [], "phi": []
    }

    for name, start, end in seasons:
        img = base.filterDate(start, end).mean()

        stats = img.reduceRegion(
            ee.Reducer.mean(),
            geometry,
            20,
            maxPixels=1e8
        ).getInfo()

        res["labels"].append(name)
        for k in ["NDVI","EVI","SAVI","DVI","SR","PHI"]:
            res[k.lower()].append(stats.get(k))

    return res
