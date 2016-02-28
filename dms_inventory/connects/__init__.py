import redis

def singleton(cls):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return _singleton


@singleton
class ConnectFactory(object):
    def getConnect(self,conn_type,config):
        if conn_type == "redis":
            host = config.get("redis","host")
            port = config.get("redis","port")
            rd = redis.Redis(host,port)
            return redis.Redis(host,port)
