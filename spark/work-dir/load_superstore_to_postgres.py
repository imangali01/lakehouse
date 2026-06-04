#!/usr/bin/env python3
"""
Load Superstore Sales Data to PostgreSQL using PySpark

This script reads superstore_sales.csv and loads data into public.superstore_sales table
in PostgreSQL connected via Docker Compose.

Usage:
    docker exec spark-master /opt/spark/bin/spark-submit \
                --master spark://spark-master:7077 \
                /opt/spark/work-dir/load_superstore_to_postgres.py
"""

from pyspark.sql import SparkSession
import sys
import os

def main():
    """Main execution function"""
    
    # ====================================================================
    # 1. Подключение библиотек и настройка SparkSession
    # ====================================================================
    print("="*80)
    print("1. Initializing Spark Session...")
    print("="*80)
    
    # Подключаемся к Spark Master, запущенному в docker-compose-spark.yaml
    # Spark Master доступен по адресу spark-master:7077 в сети lakehouse
    spark = SparkSession.builder \
        .appName("LoadSuperstore") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.1") \
        .getOrCreate()
    
    # Устанавливаем уровень логирования
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"✓ SparkSession created successfully!")
    print(f"  Spark version: {spark.version}")
    # print(f"  Master URL: {spark.sparkContext.master()}")
    print(f"  App Name: {spark.sparkContext.appName}")
    print(f"  Spark UI: http://localhost:4040")
    
    # ====================================================================
    # 2. Чтение CSV файла с помощью PySpark
    # ====================================================================
    print("\n" + "="*80)
    print("2. Reading CSV file...")
    print("="*80)
    
    # Определяем путь к CSV файлу
    csv_file_path = os.path.join("/opt/spark/work-dir/data/superstore_sales.csv")
    
    print(f"  CSV file path: {csv_file_path}")
    
    # Читаем CSV файл
    df = spark.read.csv(
        csv_file_path,
        header=True,
        inferSchema=True,
        escape='"',
        multiLine=True
    )
    
    print(f"✓ CSV file successfully loaded!")
    print(f"  Number of rows: {df.count()}")
    print(f"  Number of columns: {len(df.columns)}")
    
    # ====================================================================
    # 3. Преобразование схемы и проверка данных
    # ====================================================================
    print("\n" + "="*80)
    print("3. DataFrame Schema and Data Verification")
    print("="*80)
    
    print("\nDataFrame Schema:")
    df.printSchema()
    
    print("\nSample Data (first 5 rows):")
    df.show(5, truncate=False)
    
    print("\nColumn names:")
    print(df.columns)
    
    # ====================================================================
    # 4. Подключение к PostgreSQL через JDBC
    # ====================================================================
    print("\n" + "="*80)
    print("4. PostgreSQL Connection Configuration")
    print("="*80)
    
    # Параметры подключения к PostgreSQL
    postgres_host = "postgres"  # Имя контейнера из docker-compose.yaml
    postgres_port = 5432
    postgres_db = "postgres"
    postgres_user = "postgres"
    postgres_password = "postgres"
    postgres_table = "public.superstore_sales"
    
    # Формируем JDBC URL
    jdbc_url = f"jdbc:postgresql://{postgres_host}:{postgres_port}/{postgres_db}"
    
    # Драйвер JDBC
    jdbc_driver = "org.postgresql.Driver"
    
    print(f"PostgreSQL Connection Settings:")
    print(f"  Host: {postgres_host}")
    print(f"  Port: {postgres_port}")
    print(f"  Database: {postgres_db}")
    print(f"  Table: {postgres_table}")
    print(f"  JDBC URL: {jdbc_url}")
    
    # ====================================================================
    # 5. Создание таблицы и загрузка данных в public.superstore_sales
    # ====================================================================
    print("\n" + "="*80)
    print("5. Loading Data to PostgreSQL")
    print("="*80)
    
    try:
        print(f"\nStarting data load to PostgreSQL...")
        print(f"  Table: {postgres_table}")
        print(f"  Total records to load: {df.count()}")
        
        # Загружаем данные в PostgreSQL
        df.write \
            .format("jdbc") \
            .mode("overwrite") \
            .option("url", jdbc_url) \
            .option("dbtable", postgres_table) \
            .option("user", postgres_user) \
            .option("password", postgres_password) \
            .option("driver", jdbc_driver) \
            .save()
        
        print(f"\n{'='*80}")
        print(f"✓ Data successfully loaded to PostgreSQL!")
        print(f"✓ Table: {postgres_table}")
        print(f"✓ Records loaded: {df.count()}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n✗ Error during data load: {str(e)}")
        spark.stop()
        sys.exit(1)
    
    # ====================================================================
    # 6. Проверка загруженных данных
    # ====================================================================
    print("\n" + "="*80)
    print("6. Data Verification from PostgreSQL")
    print("="*80)
    
    try:
        # Читаем данные из PostgreSQL для проверки
        df_check = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", postgres_table) \
            .option("user", postgres_user) \
            .option("password", postgres_password) \
            .option("driver", jdbc_driver) \
            .load()
        
        print(f"\nData verification from PostgreSQL:")
        print(f"✓ Total records in table: {df_check.count()}")
        print(f"\nTable schema:")
        df_check.printSchema()
        print(f"\nFirst 5 rows:")
        df_check.show(5, truncate=False)
        
    except Exception as e:
        print(f"\n✗ Error during verification: {str(e)}")
        spark.stop()
        sys.exit(1)
    
    # ====================================================================
    # Завершение
    # ====================================================================
    print("\n" + "="*80)
    print("✓ Process completed successfully!")
    print("="*80)
    
    spark.stop()


if __name__ == "__main__":
    main()
