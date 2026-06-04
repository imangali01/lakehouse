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

