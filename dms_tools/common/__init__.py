def singleton(cls):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return _singleton

import os
from ConfigParser import SafeConfigParser
@singleton
class Config(object):
    def __init__(self):
        abs_path = os.path.abspath(__file__)
        config_home =os.path.dirname(os.path.dirname(abs_path))
        config_file = os.path.join(config_home,"resource.conf")
        self.parser = SafeConfigParser()
        self.parser.read(config_file)

    def getRundeckUrl(self):
        return self.parser.get("Rundeck","rundeck_server")

    def getRundeckToken(self):
        return self.parser.get("Rundeck","token")

    def getZookeeperAddress(self):
        return self.parser.get("Zookeeper","zk_address")

    def getDBUrl(self):
        return self.parser.get("Mysql","db_url")

from tabulate import tabulate

def print_tabulate(cls,list):
    list = map(lambda e: e.to_array(),list)
    print tabulate(list,headers=cls.listheaders())



if __name__ == '__main__':
    Config()

