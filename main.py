from datetime import datetime
import os
import logging.config
from pythonjsonlogger import jsonlogger
from prometheus_client import start_http_server
import redis
from sqlalchemy.orm import sessionmaker
from db import connect_to_db
from storage import Storage

REDIS_SERVICE_HOST = os.getenv('REDIS_SERVICE_HOST')
REDIS_SERVICE_PORT = os.getenv('REDIS_SERVICE_PORT', 6379)
REDIS_DB_NUM = os.getenv('REDIS_DB_NUM', 0)


class ElkJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(ElkJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['@timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('equityvine_logger')


def connect_to_redis():
    return redis.Redis(host=REDIS_SERVICE_HOST, port=REDIS_SERVICE_PORT, db=REDIS_DB_NUM)


def create_sql_session():
    session = sessionmaker(connect_to_db())
    return session()


if __name__ == '__main__':
    start_http_server(8080)

    REDIS_CLIENT = connect_to_redis()
    SQL_SESSION = create_sql_session()
    while True:
        storage = Storage(SQL_SESSION, REDIS_CLIENT)
        storage.read_from_redis()
        storage.store_data()
        storage.save_objects()
