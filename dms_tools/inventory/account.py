import os
import json
from StringIO import StringIO
from zkbase import ZookeeperNode
from dbbase import DBNode
from do import Tenant
from node import Node

class Account(object):
    path = "accounts"

    def __init__(self,accountId,accountName,dbobj=None):
        self.id = accountId
        self.name = accountName
        self.dbobj = dbobj


    @classmethod
    def list(cls):
        return cls.listfromdb()


    @classmethod
    def get(cls,accountId):
        db = DBNode()
        tenants = db.session.query(Tenant).filter(Tenant.id == accountId).all()
        for tenant in tenants:
            return [Account(tenant.id,tenant.name,tenant)]


    def listnodes(self):
        list = []
        services = self.dbobj.services
        for svc in services:
            nodes = svc.nodes
            for node in nodes:
                list.append(Node(node.manageip,svc.name,svc.os,node.stackid))
        return list

    @classmethod
    def listfromdb(cls):
        db = DBNode()
        list = []
        tenants = db.session.query(Tenant).all()
        print tenants
        for tenant in tenants:
            list.append(Account(tenant.id,tenant.name))
        return list


    @classmethod
    def listfromzk(cls):
        zn = ZookeeperNode()
        base_path = os.path.join(zn.root_path,cls.path)
        children = zn.getChildren(base_path)
        list = []
        for child in children:
            tenant = zn.getPath(os.path.join(base_path,child))
            znodestat = tenant[1]
            data = tenant[0]
            map = json.load(StringIO(data))
            list.append(Account(child,map["account_name"]))
        return list

    @classmethod
    def getfromzk(cls,accountId):
        zn = ZookeeperNode()
        base_path = os.path.join(zn.root_path,cls.path)

    def to_array(self):
        return [self.id,self.name]

    @classmethod
    def listheaders(cls):
        return ["id","name"]

