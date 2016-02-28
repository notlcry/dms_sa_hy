# 1. use 'ovs-ofctl dump-flows br-router table=1 | grep table=1 | grep dl_src' to get traffic info from host to vrouter,
#      dl_src as the key
# 3. use 'ovs-ofctl dump-flows br-router table=6 | grep table=6 | grep mod_dl_dst' to get traffic info from vrouter to host,
#     mod_dl_dst as the key

import subprocess
import socket
import traceback


class CmdError(Exception):
    pass


def run(cmd):
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
        (stdout, stderr) = proc.communicate()
        return stdout.split("\n")
    except Exception as err:
        raise CmdError("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))


def run_table_in_cmd(table_id="1,2"):
    in_ids = table_id.split(",")
    result = []
    for id in in_ids:
        temp = run_table_1_cmd(id)
        result.extend(temp)
    return result


def run_table_1_cmd(table_id):
    table = 'table=%s' % table_id
    cmd = 'sudo ovs-ofctl dump-flows br-router %s | grep %s | grep dl_src' % (table, table)
    lines = run(cmd)
    result = []
    for line in lines:
        if 'dl_src' in line and 'n_bytes' in line:
            result.append(line)
    return result


def parse_table_1_line(line):
    dl_src = line.split('dl_src=')[1].split(',')[0].strip()
    n_bytes = line.split('n_bytes=')[1].split(',')[0].strip()
    n_packets = line.split('n_packets=')[1].split(',')[0].strip()
    # ['ac:bc:32:8a:11:90', 0, 0]
    return [dl_src, n_bytes, n_packets]


def parse_table_in(table_id="1,2"):
    output_lines = run_table_in_cmd(table_id)
    stat_dict = {}
    for line in output_lines:
        info = parse_table_1_line(line)
        # dl_src as the key, need to add the value with the same key
        dl_src = info[0]
        n_bytes = int(info[1])
        n_packets = int(info[2])
        if stat_dict.has_key(dl_src):
            value = stat_dict.get(dl_src)
            n_bytes = value[0] + n_bytes
            n_packets = value[1] + n_packets
            stat_dict[dl_src] = [n_bytes, n_packets]
        else:
            stat_dict[dl_src] = [n_bytes, n_packets]
    # {"ac:bc:32:8a:11:90":[0, 0]}
    return stat_dict


def run_table_6_cmd(table_id=6):
    table = 'table=%s' % table_id
    cmd = 'sudo ovs-ofctl dump-flows br-router %s | grep %s | grep mod_dl_dst' % (table, table)
    lines = run(cmd)
    result = []
    for line in lines:
        if 'mod_dl_dst' in line and 'n_bytes' in line:
            result.append(line)
    return result


def parse_table_6_line(line):
    mod_dl_dst = line.split('mod_dl_dst:')[1].split(',')[0].strip()
    n_bytes = line.split('n_bytes=')[1].split(',')[0].strip()
    n_packets = line.split('n_packets=')[1].split(',')[0].strip()
    #['08:10:27:31:4f:60', 0, 0]
    return [mod_dl_dst, n_bytes, n_packets]


def parse_table_6(table_id=6):
    output_lines = run_table_6_cmd(table_id)
    stat_dict = {}
    for line in output_lines:
        info = parse_table_6_line(line)
        mod_dl_dst = info[0]
        n_bytes = int(info[1])
        n_packets = int(info[2])
        if stat_dict.has_key(mod_dl_dst):
            value = stat_dict.get(mod_dl_dst)
            n_bytes = value[0] + n_bytes
            n_packets = value[1] + n_packets
            stat_dict[mod_dl_dst] = [n_bytes, n_packets]
        else:
            stat_dict[mod_dl_dst] = [n_bytes, n_packets]
    # {"08:10:27:31:4f:60":[0,0] }
    return stat_dict


def get_host_name():
        return socket.gethostname().replace("-","_")


def get_delta_value(org_dict, latest_dict):
        # {"ac:bc:32:8a:11:90":[0,0] }
        delta_dict = {}
        for key, value in latest_dict.iteritems():
            if org_dict.has_key(key):
                org_value = org_dict.get(key)
                delta_dict[key] = [value[0] - org_value[0], value[1] - org_value[1]]
                org_dict[key] = value
            else:
                delta_dict[key] = value
                org_dict[key] = value

        for key in org_dict.keys():
            if latest_dict.has_key(key) is False:
                org_dict.pop(key)
        return delta_dict


class VRouterTrafficStatMon(object):
    def __init__(self):
        self.plugin_name = "vrouter_traffic_stat"
        self.interval = 5
        self.hostname = get_host_name()
        self.table_in_id = "1,2"
        self.table_out_id = 6
        self.verbose_logging = False
        self.account_id = None
        self.vm_type = None

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def init(self):
        self.IN_BASE_LINE = parse_table_in(self.table_in_id)
        self.OUT_BASE_LINE = parse_table_6(self.table_out_id)

    def configure_callback(self, conf):
        for node in conf.children:
            val = str(node.values[0])

            if node.key == 'HostName':
                self.hostname = val
            elif node.key == 'Interval':
                self.interval = int(float(val))
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            elif node.key == 'PluginName':
                self.plugin_name = val
            elif node.key == "AccountId":
                self.account_id = val
            elif node.key == "VmType":
                self.vm_type = val
            elif node.key == "TABLE_IN_ID":
                self.table_in_id = val
            elif node.key == "TABLE_OUT_ID":
                self.table_out_id = val
            else:
                collectd.warning('[plugin] %s: unknown config key: %s' % (self.plugin_name, node.key))

    def dispatch_value(self, plugin, host, type, type_instance, value):
        self.log_verbose("Dispatching value plugin=%s, host=%s, type=%s, type_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, value))
        val = collectd.Values(type=type)
        val.plugin = plugin
        val.host = host
        val.type_instance = type_instance
        val.interval = self.interval
        val.values = [value]
        val.dispatch()
        self.log_verbose("Dispatched value plugin=%s, host=%s, type=%s, type_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, value))

    def read_callback(self):
        try:
            in_latest_stat = parse_table_in(self.table_in_id)
            out_latest_stat = parse_table_6(self.table_out_id)
            in_delta_stat = get_delta_value(self.IN_BASE_LINE, in_latest_stat)
            out_delta_stat = get_delta_value(self.OUT_BASE_LINE, out_latest_stat)
            host = "%s__%s__%s" % (self.account_id, self.hostname, self.vm_type)
            # {"ac:bc:32:8a:11:90":[0,0] }
            for key, value in in_delta_stat.iteritems():
                self.dispatch_value(self.plugin_name, host, "dl_src_n_bytes", key, value[0])
                self.dispatch_value(self.plugin_name, host, "dl_src_n_packets", key, value[1])
            for key, value in out_delta_stat.iteritems():
                self.dispatch_value(self.plugin_name, host, "mod_dl_dst_n_bytes", key, value[0])
                self.dispatch_value(self.plugin_name, host, "mod_dl_dst_n_packets", key, value[1])
        except Exception as exp:
            self.log_verbose(traceback.print_exc())
            self.log_verbose("plugin %s run into exception" % self.plugin_name)
            self.log_verbose(exp.message)


if __name__ == '__main__':
    stat_1_1 = parse_table_in("1,2")
    stat_6_1 = parse_table_6(6)
    print '***********'
    print stat_1_1
    print stat_6_1
    import time
    time.sleep(5)
    stat_1_2 = parse_table_in("1,2")
    stat_6_2 = parse_table_6(6)
    print '***********'
    print stat_1_2
    print stat_6_2

    print '***********'
    print get_delta_value(stat_1_1, stat_1_2)
    print get_delta_value(stat_6_1, stat_6_2)
else:
    import collectd
    vrouter_status = VRouterTrafficStatMon()
    collectd.register_config(vrouter_status.configure_callback)
    collectd.register_init(vrouter_status.init)
    collectd.register_read(vrouter_status.read_callback)