from kazoo.client import KazooClient
import os
import json
from lib.services.servicecontext import ServiceContext

from .. utils import singleton

@singleton
class DMSInventoryManager(object):
    def __init__(self):
        config = ServiceContext().getConfigService()
        self.zk_address = config.get("Inventory","zk_address")
        self.root_path = config.get("Inventory","zk_root_path")
        self.zk_client = KazooClient(hosts=self.zk_address)

    def start(self):
        self.zk_client.start()

    def stop(self):
        self.zk_client.stop()
        self.zk_client.close()

    def getservice(self,accountId):
        """
        :param accountId:
        :return:
        """
        services = []
        service_path = os.path.join(self.root_path,accountId,"services")
        children = self.zk_client.get_children(service_path)
        for child in children:
            services.append(child)
        return services

    def getinstancebyservice(self,accountId,service):
        parent_path = os.path.join(self.root_path,accountId,"services",service,"instances")
        nodes = []
        children = self.zk_client.get_children(parent_path)
        for child in children:
            nodepath = os.path.join(parent_path,child)
            print nodepath
            data,stats = self.zk_client.get(nodepath)
            map = json.loads(data)
            ret = {}
            ret["vmType"] = service
            ret["accountId"] = accountId
            ret["stackId"] = map.get("id","")
            ret["vmManagementIP"] = map.get("manageip",None)
            ret["vmPublicIP"] = map.get("publicip",None)
            ret["vmServiceIP"] = map.get("serviceip",None)
            ret["eventName"] = "CREATE_VM"
            nodes.append(ret)
        return nodes


