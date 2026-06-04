# Trino Architecture

`Trino` в этом репозитории отвечает за SQL-доступ к данным lakehouse.

## Что где находится

- `docker-compose-trino.yaml` - поднимает `trino-coordinator` и `trino-worker-1/2`
- `trino-config/coordinator/config.properties` - конфигурация coordinator
- `trino-config/worker/config.properties` - конфигурация worker
- `trino-config/catalog/dlh-bronze.properties` - catalog для bronze-слоя
- `trino-config/catalog/dlh-gold.properties` - catalog для gold-слоя

## Порядок запуска

1. Поднять базовую инфраструктуру из `docker-compose.yaml`
2. Поднять `Trino`:

```bash
docker compose -f docker-compose-trino.yaml up -d
```

3. Открыть Trino UI:

```text
http://localhost:8080
```

## Роли контейнеров

- `trino-coordinator` - принимает запросы и распределяет работу
- `trino-worker-1`, `trino-worker-2` - исполняют запросы

## Связь с lakehouse

`Trino` подключается к catalog-ам через файлы в `trino-config/catalog/` и может использовать данные из общих storage-сервисов этого репозитория.

