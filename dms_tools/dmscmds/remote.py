from optparse import OptionParser
from cmdbase import Command,Subcommand,MultipleOption,SubcommandOptionParser
from sqlalchemy.orm.exc import NoResultFound
from inventory.dbbase import DBNode
from inventory.do import DMSToolTask
from inventory.account import Account
from executor.tcpdump_exec import TcpdumpExecutor

class Execute(Subcommand):
    def __init__(self):
        Subcommand.__init__(self,'start',OptionParser(option_class=MultipleOption,usage='%prog [OPTIONS]'),'running tcpdump on all the nodes of one account')
        self.parser.add_option('-a','--account',action="store",dest="accountId")
        self.parser.add_option('-f','--firewall',action = "extend",dest="firewall_interface")
        self.parser.add_option('-i','--ipsecvpn',action = "extend",dest="ipsecvpn_interface")
        self.parser.add_option('-d','--dns',action = "extend",dest="dns_interface")
        self.parser.add_option('-v','--vrouter',action = "extend",dest="vrouter_interface")

    def execute(self,options,subargs):
        if not options.accountId:
            self.parser.error("accountId is required")
        account = Account.get(options.accountId)
        if account is None or len(account) == 0:
            print "account does not exist in db"
            return
        try:
            task = DBNode().session.query(DMSToolTask).filter(DMSToolTask.accountId == options.accountId).filter(DMSToolTask.task_name== "tcpdump").one()
        except NoResultFound,e:
            map={}
            map["firewall"] = options.firewall_interface
            map["ipsecvpn"] = options.ipsecvpn_interface
            map["dns"] = options.dns_interface
            map["vrouter"] = options.vrouter_interface
            TcpdumpExecutor(account).start(map)
            task = DMSToolTask()
            task.task_name = "tcpdump"
            task.accountId = options.accountId
            DBNode().session.add(task)
            DBNode().session.commit()
        else:
            print "ERROR: have started tcpdump task on the account ,should stop it first"

class Copy(Subcommand):
    def __init__(self):
        Subcommand.__init__(self,'stop',OptionParser(option_class=MultipleOption,usage='%prog [OPTIONS]'),'stop tcpdump running on the nodes')
        self.parser.add_option('-a','--account',action="store",dest="accountId")
        pass

    def execute(self,options,subargs):
        if not options.accountId:
            self.parser.error("accountId is required")
        account = Account.get(options.accountId)
        if account is None or len(account) == 0:
            print "account does not exist in db"
            return

        try:
            task = DBNode().session.query(DMSToolTask).filter(DMSToolTask.accountId == options.accountId).filter(DMSToolTask.task_name== "tcpdump").one()
        except NoResultFound,e:
            print "Info: no tcpdump task need to stop on this accounit"
        else:
            TcpdumpExecutor(account).stop()
            DBNode().session.delete(task)
            DBNode().session.commit()


class StatusCommand(Subcommand):
    def __init__(self):
        Subcommand.__init__(self,'status',OptionParser(option_class=MultipleOption,usage='%prog [OPTIONS]'),'check the tasks staus running under customer')
        self.parser.add_option('-a','--account',action="store",dest="accountId")

    def execute(self,options,subargs):
        if not options.accountId:
            self.parser.error("accountId is required")
        account = Account.get(options.accountId)
        if account is None or len(account) == 0:
            print "account does not exist in db"
            return
        print TcpdumpExecutor(account).status()

class Remote(Command):
    def __init__(self):
        subparser = SubcommandOptionParser(subcommands=(StartCommand(),StopCommand(),StatusCommand()))
        Subcommand.__init__(self,'remote',subparser,'remote execute')

