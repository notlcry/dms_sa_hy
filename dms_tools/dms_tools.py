from dmscmds import dms_parser

if __name__ == '__main__':

# python packet_trace.py tcpdump -a -f eth0 -f eth1 -v eth0  -i eth1  -d eth2
# python packet_trace.py tcpdump
    options,subcommand,suboptions,subargs = dms_parser.parse_args()
    subcommand.execute(suboptions,subargs)
