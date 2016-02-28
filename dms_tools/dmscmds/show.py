from optparse import OptionParser
from cmdbase import Command,Subcommand,MultipleOption,SubcommandOptionParser
from inventory.account import Account
from inventory.node import Node
from common import print_tabulate
class AccountCommand(Subcommand):
    def __init__(self):
        Subcommand.__init__(self,"account",OptionParser(usage='%prog [OPTION]'),'show account info')
        self.parser.add_option('-a','--accountId',action='store',dest="accountId",default="all")

    def execute(self,options,subargs):
        if options.accountId == "all":
            print_tabulate(Account,Account.list())
        else:
            print_tabulate(Account,Account.get(options.accountId))

class NodeCommand(Subcommand):
    def __init__(self):
        Subcommand.__init__(self,"nodes",OptionParser(usage='%prog [OPTION]'),'show nodes under one account')
        self.parser.add_option('-a','--accountId',action='store',dest="accountId")

    def execute(self,options,subargs):
        if not options.accountId:
            self.parser.error("accountid is required...")
        account = Account.get(options.accountId)
        if account!= None:
            print_tabulate(Node,account[0].listnodes())
        else:
            print "Error: accountid is not exisit"

class Show(Command):
    def __init__(self):
        subparser = SubcommandOptionParser(subcommands=(AccountCommand(),NodeCommand(),))
        Subcommand.__init__(self,'show',subparser,'show inventory')
