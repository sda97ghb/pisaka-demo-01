# internal_api это на самом деле кусочек фронта, реализованный внутри бэка
# нужен он в первую очередь для оптимизации запросов, чтобы за один http запрос
# собрать данные по нескольким сущностям

from .app import InternalAPIApp, create_app

__all__ = ["create_app", "InternalAPIApp"]
