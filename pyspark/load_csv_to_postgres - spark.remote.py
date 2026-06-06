#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для загрузки данных superstore_sales в PostgreSQL с использованием PySpark.
Этот скрипт читает CSV файл и загружает данные в таблицу public.superstore_sales.
"""

import sys
from pyspark.sql import SparkSession


def main():
    # =========================================================================
    # 1. Подключение библиотек и настройка SparkSession (Spark Connect)
    # =========================================================================
    print("Инициализация SparkSession...")
    try:
        # Используем Spark Connect (подключение к удаленному/запущенному драйверу)
        spark = SparkSession.builder \
            .remote("sc://localhost:15002") \
            .appName("LoadSuperstore") \
            .getOrCreate()
            
        # Альтернативный вариант (классический Spark Standalone)
        # spark = SparkSession.builder \
        #     .master("spark://localhost:7077") \
        #     .appName("LoadSuperstore") \
        #     .config("spark.ui.port", "4043") \
        #     .getOrCreate()

        print("SparkSession успешно создан.")
        try:
            print(f"Driver host: {spark.conf.get('spark.driver.host')}")
            print(f"UI port: {spark.conf.get('spark.ui.port')}")
        except Exception:
            # При использовании Spark Connect некоторые классические конфиги 
            # могут быть недоступны напрямую через conf.get
            pass

    except Exception as e:
        print(f"Ошибка при создании SparkSession: {e}")
        sys.exit(1)

    # =========================================================================
    # 2. Чтение CSV файла с помощью PySpark
    # =========================================================================
    # Путь к CSV файлу (относительный путь от spark-driver)
    csv_file_path = "/opt/data/superstore_sales.csv"
    print(f"\nЧитаем CSV файл из: {csv_file_path} ...")

    try:
        df = spark.read.csv(
            csv_file_path,
            header=True,
            inferSchema=True,
            escape='"',
            multiLine=True
        )
        
        print("✓ CSV файл успешно загружен!")
        print(f"Количество строк: {df.count()}")
        print(f"Количество колонок: {len(df.columns)}")
        
    except Exception as e:
        print(f"Ошибка при чтении CSV файла: {e}")
        spark.stop()
        sys.exit(1)

    # =========================================================================
    # 3. Преобразование схемы и проверка данных
    # =========================================================================
    print("\n" + "="*80)
    print("Схема DataFrame:")
    df.printSchema()

    print("\n" + "="*80)
    print("Образец данных (первые 5 строк):")
    df.show(5, truncate=False)

    print("\n" + "="*80)
    print("Названия колонок:")
    print(df.columns)

    # =========================================================================
    # 4. Настройка подключения к PostgreSQL через JDBC
    # =========================================================================
    postgres_host = "postgres"
    postgres_port = 5432
    postgres_db = "postgres"
    postgres_user = "postgres"
    postgres_password = "postgres"
    postgres_table = "public.superstore_sales"

    # Формируем JDBC URL и указываем драйвер
    jdbc_url = f"jdbc:postgresql://{postgres_host}:{postgres_port}/{postgres_db}"
    jdbc_driver = "org.postgresql.Driver"

    print("\n" + "="*80)
    print("Настройки подключения к PostgreSQL:")
    print(f"Host: {postgres_host}")
    print(f"Port: {postgres_port}")
    print(f"Database: {postgres_db}")
    print(f"Table: {postgres_table}")
    print(f"JDBC URL: {jdbc_url}")
    print("="*80)

    # =========================================================================
    # 5. Создание таблицы и загрузка данных в public.superstore_sales
    # =========================================================================
    try:
        print(f"\nЗапуск загрузки данных в PostgreSQL...")
        print(f"Всего записей для загрузки: {df.count()}")
        
        # Загружаем данные в PostgreSQL (перезаписывая таблицу mode("overwrite"))
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
        print(f"✓ Данные успешно загружены в PostgreSQL!")
        print(f"✓ Таблица: {postgres_table}")
        print(f"✓ Загружено строк: {df.count()}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"Ошибка во время загрузки данных в БД: {str(e)}")
        spark.stop()
        sys.exit(1)

    # =========================================================================
    # 6. Проверка загруженных данных
    # =========================================================================
    try:
        print(f"\nПроверка данных напрямую из PostgreSQL...")
        
        # Читаем данные обратно из PostgreSQL для валидации
        df_check = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", postgres_table) \
            .option("user", postgres_user) \
            .option("password", postgres_password) \
            .option("driver", jdbc_driver) \
            .load()
        
        print(f"Успешно прочитано из БД. Всего строк в таблице: {df_check.count()}")
        print(f"\nСхема таблицы в БД:")
        df_check.printSchema()
        print(f"\nПервые 5 строк из БД:")
        df_check.show(5, truncate=False)
        
    except Exception as e:
        print(f"Ошибка во время проверки данных: {str(e)}")
    finally:
        # ОБЯЗАТЕЛЬНО закрываем SparkSession в конце работы скрипта
        print("\nЗакрытие SparkSession...")
        spark.stop()
        print("Скрипт завершил работу.")


if __name__ == "__main__":
    main()
