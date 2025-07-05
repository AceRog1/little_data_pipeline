import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

def preprocessing_part_1():
    df = pd.read_csv('~/datasets/temp/all_data.csv')
    print("Se leyo correctametne el dataset")

    df['timestamp_ingest'] = df['timestamp_ingest'].str.replace('Z', '', regex=False)

    df['timestamp_ingest'] = pd.to_datetime(df['timestamp_ingest'])

    df_modified = df.copy()

    df_modified['callsign'] = df_modified['callsign'].fillna('unidentified')

    df_modified.loc[df_modified['on_ground'] == True, 'baro_altitude'] = 0

    df_modified = df_modified.dropna()

    df_modified['baro_altitude'] = df_modified['baro_altitude'].abs()
    df_modified['velocity'] = df_modified['velocity'].abs()
    df_modified['heading'] = df_modified['heading'].abs()

    df_modified['timestamp'] = df_modified['timestamp_ingest'].dt.floor('min')

    df_modified['año'] = df_modified['timestamp'].dt.year
    df_modified['mes'] = df_modified['timestamp'].dt.month
    df_modified['dia'] = df_modified['timestamp'].dt.day
    df_modified['hora'] = df_modified['timestamp'].dt.hour
    df_modified['minuto'] = df_modified['timestamp'].dt.minute

    df_modified = df_modified.drop(['timestamp_ingest'], axis=1)

    df_modified.drop_duplicates(subset=['icao24', 'latitude', 'longitude', 'baro_altitude'], inplace=True)

    df_complete = df_modified.copy()

    LAT_MIN, LAT_MAX = -60.0, 15.0
    LON_MIN, LON_MAX = -90.0, -30.0

    QUAD_LAT_SIZE = (LAT_MAX - LAT_MIN) / 2
    QUAD_LON_SIZE = (LON_MAX - LON_MIN) / 2

    df_complete['lat_bin'] = np.floor((df_complete['latitude']  - LAT_MIN) / QUAD_LAT_SIZE).astype(int)
    df_complete['lon_bin'] = np.floor((df_complete['longitude'] - LON_MIN) / QUAD_LON_SIZE).astype(int)

    df_complete['lat_bin'] = df_complete['lat_bin'].clip(0, 1)
    df_complete['lon_bin'] = df_complete['lon_bin'].clip(0, 1)

    df_complete['zone_id'] = (df_complete['lat_bin'].astype(str) + "_" + df_complete['lon_bin'].astype(str))

    print("Se guardara en local")
    df_complete.to_csv('~/datasets/temp/preprocessing_part_1.csv', index=False)
    print("Guardado existoso")

if __name__ == "__main__":
    preprocessing_part_1()
