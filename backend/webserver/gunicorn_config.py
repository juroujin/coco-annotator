
from config import Config


bind = '0.0.0.0:80'
backlog = 2048

workers = 2
worker_class = 'eventlet'
worker_connections = 1000
timeout = 30
keepalive = 30

reload = Config.DEBUG
preload = Config.PRELOAD

errorlog = '-'
loglevel = Config.LOG_LEVEL
accesslog = None
