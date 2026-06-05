# Spark Architecture

В этом репозитории Spark используется в двух сценариях:

1. `spark-submit`-подход, где driver запускается в отдельном клиентском контейнере
2. `Spark Connect`-подход, где ноутбук или клиент подключается к уже запущенному Spark Connect server

![](./spark-architecture.drawio.svg)

Ниже я использую ваши формулировки:

- `user driver mode` - driver живет в `spark-client`
- `cluster driver mode` - работа идет через `spark-connect` и remote client

## Что где находится

- `docker-compose-spark.yaml` - Spark cluster: `spark-master` и `spark-worker-1/2/3`
- `docker-compose-spark-client.yaml` - пустой клиентский контейнер, из которого запускается `spark-submit`
- `docker-compose-spark-connect.yaml` - контейнер Spark Connect server, который подключается к уже поднятому Spark master
- `docker-compose-jupyter.yaml` - Jupyter-контейнер для подключения к Spark Connect
- `pyspark/load_csv_to_postgres.py` - пример batch job через `spark-submit`
- `pyspark/load_postgres_to_clickhouse.py` - пример batch job через `spark-submit`
- `notebooks/load_csv_to_postgres.ipynb` - пример remote connect через `SparkSession.builder.remote(...)`
- `spark/jars/` - JDBC и Spark Connect jar-файлы
- `data/superstore_sales.csv` - входной CSV-файл для примеров

## Роли контейнеров

### `docker-compose-spark.yaml`

Этот compose поднимает сам Spark cluster:

- `spark-master` - master node и точка входа к кластеру
- `spark-worker-1`, `spark-worker-2`, `spark-worker-3` - worker nodes для выполнения задач

### `docker-compose-spark-client.yaml`

Это пустой контейнер без постоянно работающего приложения.

Он нужен как место, из которого можно выполнить:

```bash
docker exec -it spark-client /opt/spark/bin/spark-submit ...
```

В этом сценарии Spark driver стартует из контейнера `spark-client`.

### `docker-compose-spark-connect.yaml`

Этот контейнер поднимает Spark Connect server.

Он уже подключен к кластеру через `spark-master`, а клиентские приложения подключаются к нему по адресу:

```python
.remote("sc://spark-connect:15002")
```

### `docker-compose-jupyter.yaml`

Jupyter нужен как удобная среда для интерактивной работы с notebook-ами.

Из него можно подключаться к уже запущенному Spark Connect server и выполнять code cells без запуска отдельного `spark-submit`.

## Порядок запуска

### 1. Поднять общую инфраструктуру

Сначала подними базовые сервисы из `docker-compose.yaml`:

- `postgres`
- `clickhouse`
- `minio`

### 2. Поднять Spark cluster

Дальше запусти:

```bash
docker compose -f docker-compose-spark.yaml up -d
```

Проверить можно по:

- Spark master UI: `http://localhost:8081`

### 3. Поднять client-контейнер

```bash
docker compose -f docker-compose-spark-client.yaml up -d
```

После этого можно запускать batch jobs:

```bash
docker exec -it spark-client /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf "spark.ui.port=4041" \
  --jars /opt/spark/jars/postgresql-42.2.23.jar,/opt/spark/jars/clickhouse-jdbc-all-0.9.8.jar \
  /opt/pyspark/load_csv_to_postgres.py
```

### 4. Поднять Spark Connect server

```bash
docker compose -f docker-compose-spark-connect.yaml up -d
```

Порты:

- `15002` - Spark Connect endpoint
- `4042` - Spark UI для connect-сервера

### 5. Поднять Jupyter

```bash
docker compose -f docker-compose-jupyter.yaml up -d
```

После этого notebook-ы из `notebooks/` можно открывать в браузере и подключаться к `spark-connect`.

## Примеры запуска

### User driver mode

Этот вариант подходит для классического batch job:

```bash
docker exec -it spark-client /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf "spark.ui.port=4041" \
  --jars /opt/spark/jars/postgresql-42.2.23.jar,/opt/spark/jars/clickhouse-jdbc-all-0.9.8.jar \
  /opt/pyspark/load_postgres_to_clickhouse.py
```

Здесь:

- driver запускается из `spark-client`
- executor-ы работают на `spark-worker-*`
- код лежит в `pyspark/`

### Cluster driver mode

Этот вариант удобен для интерактивной работы через Spark Connect:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .remote("sc://spark-connect:15002") \
    .appName("LoadSuperstore") \
    .getOrCreate()
```

Здесь:

- notebook или Jupyter выступает как клиент
- соединение идет к `spark-connect`
- код лежит в `notebooks/`
