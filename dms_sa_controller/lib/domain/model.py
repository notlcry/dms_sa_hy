from lib.utils import singleton
from lib.utils import logger

class ModelManager(object):
    def __init__(self):
        self.initmodel()


    def initmodel(self):
        self.model_base = {}
        self.model_base["basic"] = [Firewall(),VRouter(),DNS()]
        self.model_base["ipsecvpn"] = [IpsecVPN()]
        self.model_base["vpc"] = [VPC()]


    def listsvcbypath(self,pnames):
        ret = []
        for package_name in pnames:
            if self.model_base.has_key(package_name):
                ret.extend(self.model_base.get(package_name))
            else:
                logger.error("invalid package name: %s" % package_name)
        return ret

    def getsvfdefbyname(self,name):
        return ServiceBase.getServiceModel(name)


class ServiceBase(object):
    share_state = {}
    def __init__(self):
        self.type = self.__class__.__name__.lower()
        self.share_state[self.type] = self
        self.initprop()

    @classmethod
    def getServiceModel(cls,name):
        return cls.share_state.get(name,None)



@singleton
class Firewall(ServiceBase):
    def initprop(self):
        self.os = "ubuntu"
        self.instancecount = 1
        self.manage_neighbors = []
        self.service_neighbors = []



@singleton
class VRouter(ServiceBase):
    def initprop(self):
        self.os = "fedora"
        self.instancecount = 1
        self.service_neighbors = ["ipsecvpn"]
        self.manage_neighbors = ["ipsecvpn","dns"]

@singleton
class IpsecVPN(ServiceBase):
    def initprop(self):
        self.os = "centos"
        self.instancecount = 1
        self.service_neighbors=["vrouter"]
        self.manage_neighbors=["vrouter","dns"]

@singleton
class DNS(ServiceBase):
    def initprop(self):
        self.os = "ubuntu"
        self.instancecount = 1
        self.service_neighbors = []
        self.manage_neighbors = ["ipsecvpn","vrouter"]

@singleton
class VPC(ServiceBase):
    def initprop(self):
        self.os = "ubuntu"
        self.instancecount = 0
        self.manage_neighbors = []
        self.service_neighbors = []



if __name__ == '__main__':
   mm =  ModelManager()
   print mm.getsvfdefbyname("vpn")