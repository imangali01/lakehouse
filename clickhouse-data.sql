CREATE SCHEMA IF NOT EXISTS stg;

CREATE TABLE stg.superstore_sales (
    `Row ID` String,
    `Order ID` String,
    `Order Date` String,
    `Ship Date` String,
    `Ship Mode` String,
    `Customer ID` String,
    `Customer Name` String,
    `Segment` String,
    `Country` String,
    `City` String,
    `State` String,
    `Postal Code` String,
    `Region` String,
    `Product ID` String,
    `Category` String,
    `Sub-Category` String,
    `Product Name` String,
    `Sales` String
) ENGINE = MergeTree()
ORDER BY `Row ID`;

-- Загрузка данных из бакета raw
INSERT INTO stg.superstore_sales
SELECT * FROM s3(
    -- URL к вашему файлу в бакете 'raw' внутри сети Docker
    'http://minio:9002/raw/superstore_sales.csv', 
    -- Кредишлы от MinIO из вашего конфига
    'minioadmin', 
    'minioadmin', 
    -- Формат файла
    'CSVWithNames',
    -- Полная структура колонок для парсинга
    '`Row ID` String, `Order ID` String, `Order Date` String, `Ship Date` String, `Ship Mode` String, `Customer ID` String, `Customer Name` String, `Segment` String, `Country` String, `City` String, `State` String, `Postal Code` String, `Region` String, `Product ID` String, `Category` String, `Sub-Category` String, `Product Name` String, `Sales` String'
);










CREATE SCHEMA IF NOT EXISTS ods;

CREATE TABLE ods.superstore_sales (
    row_id Int64,
    order_id String,
    order_date Date,
    ship_date Date,
    ship_mode String,
    customer_id String,
    customer_name String,
    segment String,
    country String,
    city String,
    state String,
    postal_code String,
    region String,
    product_id String,
    category String,
    sub_category String,
    product_name String,
    sales Float64
) ENGINE = MergeTree()
ORDER BY (order_date, order_id);

-- SQL-скрипт для очистки и переливки
INSERT INTO ods.superstore_sales
SELECT 
    toInt64OrZero(`Row ID`) AS row_id,
    `Order ID` AS order_id,
    
    -- Заменили toDateOrZero на обычный toDate, так как parseDateTimeBestEffortOrZero уже выдает DateTime
    toDate(parseDateTimeBestEffortOrZero(`Order Date`)) AS order_date,
    toDate(parseDateTimeBestEffortOrZero(`Ship Date`)) AS ship_date,
    
    `Ship Mode` AS ship_mode,
    `Customer ID` AS customer_id,
    `Customer Name` AS customer_name,
    `Segment` AS segment,
    `Country` AS country,
    `City` AS city,
    `State` AS state,
    `Postal Code` AS postal_code,
    `Region` AS region,
    `Product ID` AS product_id,
    `Category` AS category,
    `Sub-Category` AS sub_category,
    `Product Name` AS product_name,
    toFloat64OrZero(`Sales`) AS sales
FROM stg.superstore_sales;











CREATE SCHEMA IF NOT EXISTS dds;

-- 1. Справочник Товар (SCD2)
CREATE TABLE dds.dim_products (
    product_id String,
    product_name Nullable(String),
    category Nullable(String),
    sub_category Nullable(String),
    valid_from DateTime,
    valid_to Nullable(DateTime)
) ENGINE = ReplacingMergeTree()
ORDER BY (product_id, valid_from);

INSERT INTO dds.dim_products
WITH raw AS (
    SELECT 
        product_id, 
        any(product_name) AS product_name, 
        any(category) AS category,
        any(sub_category) AS sub_category,
        now() AS __load_date
    FROM ods.superstore_sales
    WHERE product_id IS NOT NULL
    GROUP BY product_id
),
dim AS (
    SELECT 
        toNullable(product_id) as product_id,
        product_name,
        category,
        sub_category,
        valid_from
    FROM dds.dim_products FINAL
    WHERE isNull(valid_to)
)
-- ЧАСТЬ 1: Новые записи или новые версии изменившихся записей
SELECT
    raw.product_id AS product_id,
    raw.product_name AS product_name,
    raw.category AS category,
    raw.sub_category AS sub_category,
    raw.__load_date AS valid_from,
    CAST(null AS Nullable(DateTime)) AS valid_to
FROM raw
LEFT JOIN dim ON raw.product_id = dim.product_id
WHERE dim.product_id IS NULL
   OR raw.product_name != dim.product_name 
   OR raw.category != dim.category 
   OR raw.sub_category != dim.sub_category

UNION ALL

-- ЧАСТЬ 2: Закрытие старых версий
SELECT 
    dim.product_id AS product_id,
    dim.product_name AS product_name,
    dim.category AS category,
    dim.sub_category AS sub_category,
    dim.valid_from AS valid_from,   
    raw.__load_date AS valid_to     
FROM raw
INNER JOIN dim ON raw.product_id = dim.product_id
WHERE raw.product_name != dim.product_name 
   OR raw.category != dim.category 
   OR raw.sub_category != dim.sub_category;







-- 2. Справочник Клиенты (SCD2)
CREATE TABLE dds.dim_customers (
    customer_id String,
    customer_name Nullable(String),
    segment Nullable(String),
    valid_from DateTime,
    valid_to Nullable(DateTime)
) ENGINE = ReplacingMergeTree()
ORDER BY (customer_id, valid_from);


INSERT INTO dds.dim_customers
WITH raw AS (
    SELECT 
        customer_id, 
        any(customer_name) AS customer_name, 
        any(segment) AS segment,
        now() AS __load_date
    FROM ods.superstore_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
dim AS (
    SELECT
    	toNullable(customer_id) as customer_id,
        customer_name,
        segment,
        valid_from
    FROM dds.dim_customers FINAL
    WHERE isNull(valid_to)
)
-- ЧАСТЬ 1: Вставка новых/изменившихся клиентов
SELECT 
    raw.customer_id AS customer_id,
    raw.customer_name AS customer_name,
    raw.segment AS segment,
    raw.__load_date AS valid_from,
    CAST(null AS Nullable(DateTime)) AS valid_to
FROM raw
LEFT JOIN dim ON raw.customer_id = dim.customer_id
WHERE dim.customer_id IS NULL 
   OR raw.customer_name != dim.customer_name 
   OR raw.segment != dim.segment

UNION ALL

-- ЧАСТЬ 2: Закрытие старых версий
SELECT 
    dim.customer_id AS customer_id,
    dim.customer_name AS customer_name,
    dim.segment AS segment,
    dim.valid_from AS valid_from,   
    raw.__load_date AS valid_to     
FROM raw
INNER JOIN dim ON raw.customer_id = dim.customer_id
WHERE raw.customer_name != dim.customer_name 
   OR raw.segment != dim.segment;





-- 3. Таблица фактов продаж
CREATE TABLE dds.fact_sales (
    row_id Int64,
    order_id String,
    order_date Date,
    ship_date Date,
    ship_mode String,
    customer_id String,
    product_id String,
    country String,
    city String,
    state String,
    postal_code String,
    region String,
    sales Float64,
    __load_date DateTime
) ENGINE = MergeTree()
ORDER BY (order_date, order_id);




INSERT INTO dds.fact_sales
SELECT 
    ods.row_id,
    ods.order_id,
    ods.order_date,
    ods.ship_date,
    ods.ship_mode,
    ods.customer_id,
    ods.product_id,
    ods.country,
    ods.city,
    ods.state,
    ods.postal_code,
    ods.region,
    ods.sales,
    now() AS __load_date
FROM ods.superstore_sales ods
INNER JOIN dds.dim_products p ON ods.product_id = p.product_id AND isNull(p.valid_to)
INNER JOIN dds.dim_customers c ON ods.customer_id = c.customer_id AND isNull(c.valid_to);




