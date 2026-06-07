# Lakehouse

Этот репозиторий показывает учебный lakehouse-стек, собранный через Docker Compose.

В проекте используются:

- `PostgreSQL` как рабочая реляционная БД и источник данных для примеров
- `ClickHouse` как аналитическое хранилище
- `MinIO` как S3-совместимое объектное хранилище
- `Trino` как SQL-движок для федеративных запросов
- `Spark` как ETL/processing-слой

## Документация

- [Spark architecture and startup guide](docs/spark.md)
- [Trino architecture and startup guide](docs/trino.md)

## Быстрый старт

Скачайте все нужные драйверы для spark и положите в папку ./spark/jars/

```
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
wget https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.9.8/clickhouse-jdbc-0.9.8-all.jar
wget https://repo1.maven.org/maven2/io/trino/trino-jdbc/472/trino-jdbc-472.jar
wget https://repo1.maven.org/maven2/org/postgresql/postgresql/42.2.23/postgresql-42.2.23.jar
wget https://repo1.maven.org/maven2/org/apache/spark/spark-connect_2.12/3.5.1/spark-connect_2.12-3.5.1.jar
```

Рекомендуемый порядок запуска:

1. Поднять базовую инфраструктуру: `docker-compose.yaml`
2. Поднять `Trino`: `docker-compose-trino.yaml`
3. Поднять Spark-кластер: `docker-compose-spark.yaml`
4. Поднять Spark client-контейнер для `spark-submit`: `docker-compose-spark-client.yaml`
5. Поднять Spark Connect server: `docker-compose-spark-connect.yaml`
6. Поднять Jupyter для remote connect: `docker-compose-jupyter.yaml`

После этого можно:

- запускать batch jobs через `spark-submit` из `pyspark/`
- открывать ноутбуки в `notebooks/` и подключаться к `spark-connect`

