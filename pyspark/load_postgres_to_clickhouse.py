"""
Load Superstore Sales from PostgreSQL to ClickHouse using PySpark

This script reads data from the PostgreSQL table public.superstore_sales
and writes it into the ClickHouse table default.superstore_sales

Usage:

docker exec -it spark-client /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf "spark.ui.port=4041" \
  --jars /opt/spark/jars/postgresql-42.2.23.jar,/opt/spark/jars/clickhouse-jdbc-all-0.9.8.jar \
  /opt/pyspark/load_postgres_to_clickhouse.py
"""

from pyspark.sql import SparkSession
import sys

def main():
    print("=" * 80)
    print("1. Initializing Spark Session...")
    print("=" * 80)
    
    # Инициализируем классическую сессию для работы через spark-submit
    spark = SparkSession.builder \
        .appName("PostgresToClickHouse") \
        .getOrCreate()

    print(f"✓ SparkSession created successfully! Spark version: {spark.version}")

    # --- НАСТРОЙКИ POSTGRESQL ---
    postgres_url = "jdbc:postgresql://postgres:5432/postgres" 
    postgres_properties = {
        "user": "postgres",
        "password": "postgres",
        "driver": "org.postgresql.Driver"
    }
    postgres_table = "public.superstore_sales"

    # --- НАСТРОЙКИ CLICKHOUSE ---
    clickhouse_url = "jdbc:clickhouse://clickhouse:8123/default"
    clickhouse_properties = {
        "user": "admin",
        "password": "admin",
        "driver": "com.clickhouse.jdbc.ClickHouseDriver",
        # Опция указывает Spark, какие параметры дописать в конец CREATE TABLE
        "createTableOptions": "ENGINE = MergeTree ORDER BY `Row ID`"
    }
    clickhouse_table = "default.superstore_sales"

    print("\n" + "=" * 80)
    print(f"2. Reading data from PostgreSQL table: {postgres_table}...")
    print("=" * 80)

    try:
        # Читаем данные из Postgres
        df = spark.read.jdbc(
            url=postgres_url, 
            table=postgres_table, 
            properties=postgres_properties
        )
        
        row_count = df.count()
        print(f"✓ Successfully read {row_count} rows from PostgreSQL.")
        print("--- Data Schema ---")
        df.printSchema()

    except Exception as e:
        print(f"❌ Error while reading from PostgreSQL: {e}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"3. Writing data to ClickHouse table: {clickhouse_table}...")
    print("=" * 80)

    try:
        # Если таблицы нет, Spark создаст её автоматически, маппя типы данных.
        # Опция "createTableOptions" добавит ENGINE в конец SQL-запроса.
        df.write.jdbc(
            url=clickhouse_url, 
            table=clickhouse_table, 
            mode="append", 
            properties=clickhouse_properties
        )
        print("✓ Data successfully written to ClickHouse!")

    except Exception as e:
        print(f"❌ Error while writing to ClickHouse: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
