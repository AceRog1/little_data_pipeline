import pandas as pd
import glob
import os

RAW_PATH = "data/raw/*.csv"
PROCESSED_PATH = "data/processed/congestion_minute.parquet"

def clean_and_transform():
    all_files = glob.glob(RAW_PATH)
    df_list = []

    for file in all_files:
        df = pd.read_csv(file, parse_dates=["timestamp_ingest"], date_parser=lambda x: pd.to_datetime(x.rstrip('Z')))
        

        if df["timestamp_ingest"].dt.tz is None:
            df["timestamp_ingest"] = df["timestamp_ingest"].dt.tz_localize("UTC")
        df["timestamp_ingest"] = df["timestamp_ingest"].dt.tz_convert("America/Lima")  

        df["minute"] = df["timestamp_ingest"].dt.floor("min")  
        
        congestion = df.groupby("minute")["icao24"].nunique().rename("congestion").to_frame()
        df_list.append(congestion)

    final_df = pd.concat(df_list)
    final_df = final_df.sort_index()  
    
    final_df.to_parquet(PROCESSED_PATH)
    print(f"✅ Datos procesados guardados en {PROCESSED_PATH}")

if __name__ == "__main__":
    clean_and_transform()
