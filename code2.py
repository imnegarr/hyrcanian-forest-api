import ee


def run_forest_model(start_date, end_date):
    geometry = ee.Geometry.Rectangle([48.87, 38.30, 48.88, 38.31])
    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterDate(start_date, end_date)
        .filterBounds(geometry)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    )
    image = collection.first()
    if image is None:
        return None
    image = ee.Image(image).clip(geometry)
    nir = image.select('B8')
    red = image.select('B4')
    blue = image.select('B2')
    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': nir, 'RED': red, 'BLUE': blue}
    ).rename('EVI')
    savi = image.expression(
        '((NIR - RED) * 1.5) / (NIR + RED + 0.5)',
        {'NIR': nir, 'RED': red}
    ).rename('SAVI')
    dvi = nir.subtract(red).rename('DVI')
    sr = nir.divide(red).rename('SR')
    phi = nir.divide(red.add(blue)).rename('PHI')

    return {
        'NDVI': ndvi,
        'EVI': evi,
        'SAVI': savi,
        'DVI': dvi,
        'SR': sr,
        'PHI': phi
    }
