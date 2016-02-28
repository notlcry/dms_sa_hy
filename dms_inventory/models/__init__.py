import json
from connects import ConnectFactory

class ObjectFactory(type):
    meta_data = {}
    def __init__(cls,classname,bases,dict_):
        type.__init__(cls,classname,bases,dict_)
        if 'register' not in cls.__dict__:
            cls.meta_data[classname.lower()] = cls

    @classmethod
    def fromjson(cls,json_str):
        map = json.loads(json_str)
        return cls.meta_data[map["module"]](map)


class_dict = dict(register=True)

class ModelBase(object):
    def __init__(self,map):
        self.accountId = map["accountId"]
        self.operation = map["operation"]
        self.data = map["data"]
        self.fromMap(self.data)

    def fromMap(self,data):
        pass

    def execute(self,client):
        pass

Model = ObjectFactory("Model",(ModelBase,),class_dict)


class UserGroup(Model):
    def __init__(self,map):
        super(UserGroup, self).__init__(map)

    def fromMap(self,data):
        self.groupname = data["groupname"]
        self.id = data["id"]

    def execute(self,client):
        if self.operation == "update":
            User.updateGroupName(client,self)
        elif self.operation == "delete":
            User.deleteGroupName(client,self)

class User(Model):
    def __init__(self,map):
        super(User,self).__init__(map)

    def fromMap(self,data):
        self.group_name = data.get("groupName",None)
        self.user_name = data.get("name",None)
        self.group_id = data.get("groupId",None)
        self.user_id = data.get("id",None)

    def execute(self,client):
        key_Group = self.accountId + "_" + self.user_name + "_Group"
        meta_Group = self.accountId + "_" + self.group_id + "_" + "GroupId2UserName"
        meta_UserName2Id = self.accountId + "_" + self.user_id + "_" + "UserName"

        if self.operation == "create":
            client.set(key_Group,self.group_name)
            client.hset(meta_Group,self.user_name,self.user_name)
            client.set(meta_UserName2Id,self.user_name)

        elif self.operation == "update":
            name = client.get(meta_UserName2Id)
            name_Group = self.accountId + "_" + name + "_Group"
            client.delete(name_Group)
            client.set(key_Group,self.group_name)
            client.hdel(meta_Group,name)
            client.hset(meta_Group,self.user_name)

        elif self.operation == "delete":
            client.delete(key_Group)
            client.delete(meta_UserName2Id)
            client.hdel(meta_Group,self.user_name,self.user_name)


    @classmethod
    def updateGroupName(cls,client,group):
        regex_user = group.accountId + "_" + group.id + "_GroupId2UserName"
        ret = client.hkeys(regex_user)
        for name in ret:
            key_Group = group.accountId + "_" + name + "_Group"
            client.set(key_Group,group.groupname)

    @classmethod
    def deleteGroupName(cls,client,group):
        regex_user = group.accountId + "_" + group.id + "_GroupId2UserName"
        client.hdel(regex_user)

class Account(Model):
    def __init__(self,map):
        super(Account,self).__init__(map)

    def fromMap(self,data):
        self.accountName = data["accountName"]


    def execute(self,client):
        key_Name = self.accountId + "_Name"
        if self.operation == "create" or self.operation == "update":
            client.set(key_Name,self.accountName)
        elif self.operation == "delete":
            client.delete(key_Name)
        pass

class Host(Model):
    def __init__(self,map):
        super(Host,self).__init__(map)

    def fromMap(self,data):
        self.groupName = data.get("groupName",None)
        self.mac = data.get("mac",None)
        self.user_id = data.get("userID",None)
        self.user_name = data.get("user_name",None)
        self.ip = data.get("ip",None)
        #TUNNELHOST or SERVER
        self.type = data.get("type",None)
        if self.groupName is not None and self.groupName == "default":
            self.user_name = "Unauthorize"

    def execute(self,client):
        key_User = self.accountId + "_" + self.ip + "_User"
        key_Mac = self.accountId + "_" + self.mac + "_User"
        if self.operation == "create" or self.operation == "update":
            client.set(key_User,self.user_name)
            client.set(key_Mac,self.user_name)
        elif self.operation == "delete":
            client.delete(key_User)
            client.delete(key_Mac)

    @classmethod
    def updateUserName(cls,client,user):
        regex_key = user.accountId + "*" + "_Group"
        ret = client.get(regex_key)
        for index in ret:
            client.set(index,user.user_name)




class VPN(Model):
    def __init__(self,map):
        super(VPN, self).__init__(map)

    def fromMap(self,data):
        self.userName = data.get("userName",None)
        self.ip = data.get("ip")

    def execute(self,client):
        key_User = self.accountId + "_" + self.ip + "_User"
        if self.operation == "create" or self.operation == "update":
            client.set(key_User,self.userName)
        elif self.operation == "delete":
            client.delete(key_User)

if __name__ == '__main__':

    json_usergroup = """
        {"accountId":"6bcd0ebf-a099-48aa-954c-38fa2732cade","module":"usergroup","operation":"create","result":"success","data":{"groupname":"eng","id":"cee2c7bf-24bf-4b45-8fe3-5c5854964f0e","accountUUID":"6bcd0ebf-a099-48aa-954c-38fa2732cade"}}
       """
    print ObjectFactory.fromjson(json_usergroup)

    json_user = """
         {"accountId":"0c9ec421-bf17-41e5-ae1b-5e78790ce8dc","module":"user","operation":"create","result":"success","data":{"name":"dev0","groupId":"1a85c112-277f-4a05-a56d-5be7fbd33e45","groupName":"eng","email":"dev0@test.com","id":"fe5b1adf-28d3-454c-b4c9-f5185e926bae","accountUUID":"0c9ec421-bf17-41e5-ae1b-5e78790ce8dc"}}
         """

    print ObjectFactory.fromjson(json_user)

    json_host= """
    {"accountId":"0c9ec421-bf17-41e5-ae1b-5e78790ce8dc","module":"host","operation":"create","result":"success","data":{"mac":"ac:bc:32:d4:d1:4b","userID":"fe5b1adf-28d3-454c-b4c9-f5185e926bae","ip":"10.0.0.10","user_name":"dev0","type":"TUNNELHOST","importedLine":0,"id":"856676c1-7d49-47e8-8dc1-66d6f9e3e46b"}}
    """
    print ObjectFactory.fromjson(json_host)

    json_vpn = """
    {"accountId":"0c9ec421-bf17-41e5-ae1b-5e78790ce8dc","module":"vpn","operation":"delete","result":"success","data":{"userName":"dev0","ip":"10.0.130.1/32"}}
    """

    print ObjectFactory.fromjson(json_vpn)

