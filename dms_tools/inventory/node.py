class Node(object):
    def __init__(self,name,vmtype,os,stackid):
        self.name = name
        self.vmtype = vmtype
        self.os = os
        self.stackid = stackid

    def to_array(self):
        return [self.name,self.vmtype,self.os,self.stackid]

    @classmethod
    def listheaders(cls):
        return ["name","service","os","stackid"]