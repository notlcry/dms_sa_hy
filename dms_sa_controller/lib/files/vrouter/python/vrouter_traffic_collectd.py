#!/usr/bin/env python
#coding=utf-8

import socket
import subprocess
import traceback


class CmdError(Exception):
    pass


class VRouterTraffic(object):
    def __init__(self):
        self.init_table1 = self.parse_table1()

    def parse_table1(self):
        table1_output = self._get_table1_output()
        result = {}
        for line in table1_output:
            nw_src = pick_field(line, "nw_src=", " ")
            dl_src = pick_field(line, "dl_src=", ",")
            n_packets = pick_field(line, "n_packets=", ",")
            n_bytes = pick_field(line, "n_bytes=", ",")
            result[nw_src] = [dl_src, n_packets, n_bytes]
        #{"10.1.4.77":['ac:bc:32:98:c4:83', 513, 66011], }
        return result

    def get_table1_delta(self):
        latest = self.parse_table1()
        delta = {}
        for key, value in latest.iteritems():
            if self.init_table1.has_key(key):
                old_value = self.init_table1.get(key)
                #assume mac is always the same if ip doesn't change!
                delta[key] = [value[0], int(value[1]) - int(old_value[1]), int(value[2]) - int(old_value[2])]
                self.init_table1[key] = value
            else:
                delta[key] = value

        for key in self.init_table1.keys():
            if not latest.has_key(key):
                self.init_table1.pop(key, None)
        return delta

    def _get_table1_output(self):
        '''
        cmd to generate user info,
        '''
        org_result = self._run("sudo ovs-ofctl dump-flows br-router table=1")
        result = []
        for line in org_result:
            if 'table=1' in line and 'nw_src' in line and 'dl_src' in line:
                result.append(line)
        return result

    def _run(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
            (stdout, stderr) = proc.communicate()
            output = stdout.split('\n')
            print("cmd %s output is %s" % (cmd, output))
            return output
        except Exception as err:
            raise CmdError("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))


def pick_field(org_str, first_separator, second_separator, first_index=1, second_index=0):
    field = org_str.split(first_separator)[first_index].split(second_separator)[second_index]
    return field


def get_host_name():
        return socket.gethostname().replace("-","_")


class VRouterTrafficMon(object):
    def __init__(self):
        self.plugin_name = "vrouter_traffic"
        self.interval = 5
        self.hostname = get_host_name()
        self.account_id = None
        self.vm_type = None
        self.verbose_logging = False

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def configure_callback(self, conf):
        for node in conf.children:
            val = str(node.values[0])
            if node.key == 'HostName':
                self.hostname = val
            elif node.key == 'Interval':
                self.interval = int(float(val))
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            elif node.key == "AccountId":
                self.account_id = val
            elif node.key == "VmType":
                self.vm_type = val
            elif node.key == "PluginName":
                self.plugin_name = val
            else:
                collectd.warning('[plugin] %s: unknown config key: %s' % (self.plugin_name, node.key))

    def dispatch_value(self, plugin, host, type, type_instance, plugin_instance, value):
        self.log_verbose("Dispatching value plugin=%s, host=%s, type=%s, type_instance=%s, plugin_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, plugin_instance, str(value)))
        val = collectd.Values(type=type)
        val.plugin = plugin
        val.host = host
        val.type_instance = type_instance
        val.plugin_instance = plugin_instance
        val.values = [value]
        val.dispatch()
        self.log_verbose("Dispatched value plugin=%s, host=%s, type=%s, type_instance=%s, plugin_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, plugin_instance, str(value)))

    def read_callback(self):
        try:
            self.log_verbose("plugin %s read callback called" % self.plugin_name)
            vrouter_traffic = VRouterTraffic()
            statuses = vrouter_traffic.get_table1_delta()
            #{"nw_src":['dl_src', n_packets, n_bytes]
            #{"10.1.4.77":['ac:bc:32:98:c4:83', 513, 66011], }
            for key, value in statuses.iteritems():
                #type_instance=10.1.4.77
                #plugin_instance=ac:bc:32:98:c4:83
                #type=n_packets or n_bytes
                host = "%s__%s__%s" % (self.account_id, self.hostname, self.vm_type)
                self.dispatch_value(self.plugin_name, host, 'n_packets', key, value[0], value[1])
                self.dispatch_value(self.plugin_name, host, 'n_bytes', key, value[0], value[2])

        except Exception as exp:
            self.log_verbose(traceback.print_exc())
            self.log_verbose(exp.message)


if __name__ == '__main__':
    vpn_status = VRouterTraffic()
    result = vpn_status.get_table1_delta()
    print str(result)
else:
    import collectd
    vrouter_mon = VRouterTrafficMon()
    collectd.register_config(vrouter_mon.configure_callback)
    collectd.register_read(vrouter_mon.read_callback)

