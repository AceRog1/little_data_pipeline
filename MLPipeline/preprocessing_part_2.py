import pandas as pd
import numpy as np
from pyproj import Proj, transform
from sklearn.preprocessing import StandardScaler
import joblib
import geopandas as gpd
from pathlib import Path

def preprocessing_part_2():
    df = pd.read_csv('~/datasets/temp/preprocessing_part_1.csv')
    print("Se leyo correctametne la data")

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df['time_minutes'] = df['timestamp'].dt.hour * 60 + df['timestamp'].dt.minute

    utm_proj = Proj(proj='utm', zone=20, south=True, ellps='WGS84')
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    gdf = gdf.to_crs(utm_proj.srs)
    df['x_km'] = gdf.geometry.x / 1_000
    df['y_km'] = gdf.geometry.y / 1_000
    df['altitude_km'] = df['baro_altitude'] / 1_000

    selected_features = ['x_km', 'y_km', 'altitude_km', 'time_minutes']

    scaler_path = Path.home() / 'DENStream_scaler' / 'scaler.pkl'
    if scaler_path.exists():
        print("Se encontro un Scaler")
        scaler = joblib.load(scaler_path)
    else:
        print("No se encontro el Scaler, se creara uno y se guardara")
        scaler = StandardScaler()
        scaler.fit(df[selected_features])
        joblib.dump(scaler, scaler_path)
    df_scaled = scaler.transform(df[selected_features])

    df_scaled = pd.DataFrame(df_scaled, columns=selected_features)

    df_scaled.to_csv('~/datasets/temp/preprocessing_part_2.csv', index=False)
    print("Se guardo existosamente")

if __name__ == "__main__":
    preprocessing_part_2()

