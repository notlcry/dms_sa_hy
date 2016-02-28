from .. exceptions import *

class EventFactory(type):

    meta_data = {}

    def __init__(cls,classname,bases,dict_):
        type.__init__(cls,classname,bases,dict_)
        if 'register' not in cls.__dict__:
            cls.meta_data[classname] = cls

    @classmethod
    def getEvent(cls,name,map):
        return cls.meta_data[name](map)



class_dict = dict(register=True)

def validate(meta_props,map):
    if map["accountId"] is None:
        raise InputError("accountId is None")

Event = EventFactory("Event",(object,),class_dict)



class PACKAGE_ACTIVATE(Event):
    def __init__(self,map):
        meta_props = ["topic","packageName","accountId","eventName"]
        validate(meta_props,map)
        for prop in meta_props:
            setattr(self,prop,map[prop])

class CREATE_VM(Event):
    def __init__(self,map):
        meta_props = ["eventName","topic","accountId","stackId","vmType","vmManagementIP","vmPublicIP","vmServiceIP"]
        validate(meta_props,map)
        for prop in meta_props:
            setattr(self,prop,map[prop])

class TENANT_CHECK(Event):
    def __init__(self,map):
        meta_props = ["eventName","accountId"]
        validate(meta_props,map)
        for prop in meta_props:
            setattr(self,prop,map[prop])

class TENANT_SAENABLE(Event):
    def __init__(self,map):
        meta_props = ["eventName","accountId"]
        validate(meta_props,map)
        for prop in meta_props:
            setattr(self,prop,map[prop])

class TENANT_DELETE(Event):
    def __init__(self,map):
        meta_props = ["eventName","accountId"]
        validate(meta_props,map)
        for prop in meta_props:
            setattr(self,prop,map[prop])

#TBD: the alogrithm is comlex
class PING_TIMEOUT(Event):
    def __init__(self,map):
        meta_props = ["eventName","accountId","fping_type","src_ip","dst_ip"]
        validate(meta_props,map)
        for prop in meta_props:
            setattr(self,prop,map[prop])