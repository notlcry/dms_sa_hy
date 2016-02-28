from common import singleton
from common import Config
from kazoo.client import KazooClient

@singleton
class ZookeeperNode(object):
    root_path = "/dso"
    def __init__(self):
        self.zk_client = KazooClient(hosts=Config().getZookeeperAddress())
        self.zk_client.start()

    def start(self):
        self.zk_client.start()

    def stop(self):
        self.zk_client.stop()

    def getChildren(self,path):
        return self.zk_client.get_children(path)

    def getPath(self,path):
        return self.zk_client.get(path)