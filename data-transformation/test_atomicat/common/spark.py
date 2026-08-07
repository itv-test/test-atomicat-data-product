from pyspark.sql import SparkSession


def create_spark_session() -> SparkSession:
    return (
        SparkSession
        .builder
        .appName("Example Spark App")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog"
        )
        .getOrCreate()
    )
