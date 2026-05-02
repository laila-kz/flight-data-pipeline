# the transform / process step of the pipeline : takes the ingested data and computes statistics on it

from pyspark.sql.functions import count, countDistinct, max

def flight_stats(df):
    stats = df.agg(
        count("*").alias("num_events"),
        countDistinct("icao24").alias("distinct_aircraft"),
        max("velocity").alias("max_velocity")
    )
    return stats


# aircraft by country
def aircraft_by_country(df):
    return (
        df.groupBy("origin_country")
        .agg(countDistinct("icao24").alias("num_aircraft"))
        .orderBy("num_aircraft", ascending=False)
    )

#fastest flights 
from pyspark.sql.functions import col 
def fastest_flights(df):
    return df.orderBy(col("velocity").desc()).limit(10)



#flights on ground
def flights_on_ground(df):
    return df.filter(col("on_ground") == True)


