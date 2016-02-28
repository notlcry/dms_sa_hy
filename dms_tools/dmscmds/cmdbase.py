from optparse import OptionParser,Option
import textwrap

class MultipleOption(Option):
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            values.ensure_value(dest, []).append(value)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)

class Subcommand(object):
    def __init__(self,name,parser=None,help='',aliases=()):
        self.name = name
        self.parser = parser or OptionParser(option_class=MultipleOption)
        self.aliases = aliases
        self.help = help
    def execute(self,suboptions,subargs):
        pass


class SubcommandOptionParser(OptionParser):
    _HelpSubcmd = Subcommand('help',help='command usage',aliases=('?',))

    def __init__(self,*args,**kwargs):
        self.subcmds = list(kwargs.pop('subcommands',[]))
        self.subcmds.append(self._HelpSubcmd)
        if 'usage' not in kwargs:
            kwargs['usage'] = """
            %prog COMMAND [ARGS...]
            %prog help COMMAND
            """
        OptionParser.__init__(self,*args,**kwargs)
        for cmd in self.subcmds:
            cmd.parser.prog = "%s %s" % (self.get_prog_name(),cmd.name)
        self.disable_interspersed_args()

    def add_subcommand(self,cmd):
        self.subcmds.append(cmd)

    def format_help(self, formatter=None):
        out = OptionParser.format_help(self,formatter)
        if formatter is None:
            formatter =self.formatter
        result = ["\n"]
        result.append(formatter.format_heading('Commands'))
        formatter.indent()

        disp_names = []
        help_position = 0
        for cmd in self.subcmds:
            name = cmd.name
            if cmd.aliases:
                name += ' (%s)' % ', '.join(cmd.aliases)
            disp_names.append(name)
            proposed_help_position = len(name) + formatter.current_indent
            if proposed_help_position <= formatter.max_help_position:
                help_position = max(help_position,proposed_help_position)

        for subcmd,name in zip(self.subcmds,disp_names):
            name_width = help_position - formatter.current_indent - 2
            if len(name) > name_width:
                name = "%*s%s\n" % (formatter.current_indent, "", name)
                indent_first = help_position
            else:
                name = "%*s%-*s  " % (formatter.current_indent, "",
                                      name_width, name)
                indent_first = 0
            result.append(name)
            help_width = formatter.width - help_position
            help_lines = textwrap.wrap(subcmd.help, help_width)
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (help_position, "", line)
                           for line in help_lines[1:]])
        formatter.dedent()

        # Concatenate the original help message with the subcommand
        # list.
        return out + "".join(result)


    def _subcommand_for_name(self, name):
        for subcommand in self.subcmds:
            if name == subcommand.name or name in subcommand.aliases:
                return subcommand

        return None

    def parse_args(self, a=None, v=None):

        options, args = OptionParser.parse_args(self, a, v)

        if not args:
            # No command given.
            self.print_help()
            self.exit()
        else:
            cmdname = args.pop(0)
            subcommand = self._subcommand_for_name(cmdname)
            if not subcommand:
                self.error('unknown command ' + cmdname)

        if isinstance(subcommand.parser,SubcommandOptionParser):
            if not args:
                self.print_help()
                self.exit()
            else:
                sec = args.pop(0)
                seccmd = subcommand.parser._subcommand_for_name(sec)
                secoption,secargs = seccmd.parser.parse_args(args)
                return options,seccmd,secoption,secargs
        else:

            suboptions, subargs = subcommand.parser.parse_args(args)

            if subcommand is self._HelpSubcmd:
                if subargs:
                    cmdname = subargs[0]
                    helpcommand = self._subcommand_for_name(cmdname)
                    helpcommand.parser.print_help()
                    self.exit()
                else:
                    # general
                    self.print_help()
                    self.exit()

            return options, subcommand, suboptions, subargs

class CmdFactory(type):
    cmds = {}
    def __init__(cls,classname,bases,dict_):
        type.__init__(cls,classname,bases,dict_)
        if 'register' not in cls.__dict__:
            cls.cmds[classname] = cls()

    @classmethod
    def listcmds(cls):
        return cls.cmds.values()


class_dict = dict(register=True)
Command = CmdFactory("Command",(Subcommand,),class_dict)
