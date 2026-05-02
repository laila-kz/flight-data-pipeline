# another step in the data pipeline, this time to clean the data and make it ready for analysis

def clean_flights(df):
    # remove rows with null values in important columns
    df_clean = df.dropna(subset=["icao24", "origin_country", "velocity"])
    
    # filter out unrealistic velocities (e.g., greater than 1000 m/s)
    df_clean = df_clean.filter(df_clean.velocity < 1000)
    
    return df_clean

