from rundeckbase import RundeckNode
import time
import executils
import string
import random
import os
from tabulate import tabulate
import json

def parseoption(option,flag):
    if option is None:
        return None
    arrays = option.strip().split(" ")
    for index,item in enumerate(arrays):
        if item.strip() == flag:
            for idx in range(index+1,len(arrays)):
                if arrays[idx].strip() != "":
                    return arrays[idx]
    return None

class TcpdumpExecutor(object):
    def __init__(self,account):
        self.account = account[0]
        self.nodes = account[0].listnodes()
        self.client = RundeckNode().client

    def start(self,eth_config):
        shell_cmd = "if sudo [ -d /tmp/tcpdump ];then sudo rm -rf /tmp/tcpdump;fi;sudo mkdir /tmp/tcpdump"
        if (executils.sync_runadhoc(self.client,"dms-sa",shell_cmd,tags=self.account.id) < 0):
            return
        nodemap = {}
        for node in self.nodes:
            nodemap[node.vmtype] = node
        ids = []
        cmd = "nohup sudo tcpdump %s -w %s > /dev/null 2>&1 &"
        for k,v in eth_config.iteritems():
            if v is None:
                continue
            node = nodemap[k]
            for command in v:
                interface = parseoption(command,"-i")
                writefile = parseoption(command,"-w")
                if writefile != None:
                    print "should not identify the output file"
                    continue
                if interface is None:
                    print "should identify the interface"
                    continue
                outfile = "/tmp/tcpdump/%s.cap" % interface
                print "remote command %s" % ( cmd % (command,outfile) )
                ids.append(self.client.run_adhoc_command("dms-sa",
                           cmd % (command,outfile),
                             name= node.name))

        if (executils.wait_adhoc(self.client,ids) < 0):
            return




    def stop(self):
        shell_cmd = "sudo pkill -f tcpdump"
        if(executils.sync_runadhoc(self.client,"dms-sa",shell_cmd,tags=self.account.id)<0):
            return

        random_dir = ''.join(random.sample(string.ascii_letters+string.digits, 8))
        random_path = "/tmp/fileserver/%s" % random_dir
        copy_cmd_tp = "if ! sudo [ -d %s ]; then sudo mkdir -p %s;fi; sudo scp   -oUserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=quiet -i /opt/rundeck-lib/dms.key " \
                      " %s:/tmp/tcpdump/*.cap  %s; echo 'successful'"
        ids = []
        for node in self.nodes:
            host = node.os + "@" + node.name
            node_path = os.path.join(random_path,node.vmtype)
            ids.append(self.client.run_adhoc_command("dms-sa",copy_cmd_tp%(node_path,node_path,host,node_path)))

        if(executils.wait_adhoc(self.client,ids) < 0 ):
            return
        link = "http://10.74.113.101:8000/%s" % random_dir
        print "tcpdump files collect successfully, please refer to this link: %s" % link


    def status(self):
        shell_cmd = "sudo ps -ef | grep tcpdump | grep -v grep | wc -l"
        id = executils.sync_runadhoc(self.client,"dms-sa",shell_cmd,tags=self.account.id)
        if(id < 0):
            return
        result = self.client.get_execution_output(id,fmt="json",raw=True)
        result = json.loads(result)
        execcompleted = result["execCompleted"]
        hasFailedNodes = result["hasFailedNodes"]
        execState = result["execState"]
        entries = result["entries"]
        ret = {}
        for entry in entries:
            log = entry["log"]
            node = entry["node"]
            if log.find("unable to resolve host") != -1:
                continue
            try:
                res_code = int(log)
                ret[node] = res_code
            except:
                print "node (%s) result is unexpected: %s" % (node,log)
        node_type = {}
        for node in self.nodes:
            node_type[node.name] = node.vmtype

        table=[]
        for key,value in ret.iteritems():
            item = []
            item.append(key)
            item.append(node_type[key])
            if value == 0:
                value = "not running"
            else:
                value = "running"
            item.append(value)
            table.append(item)
        headers = ["node","type","state"]
        return tabulate(table, headers)
