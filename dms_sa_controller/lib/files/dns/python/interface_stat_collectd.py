#!/usr/bin/env python
#coding=utf-8

import socket
import subprocess
import traceback


class CmdError(Exception):
    pass


class IfconfigStatus(object):
    def __init__(self, interfaces="eth0,eth1"):
        self.interfaces = interfaces.split(',')

    def get_all_interface_stats(self):
        stat_dict = {}
        for interface in self.interfaces:
            stat_dict[interface] = self._get_interface_status(interface)
        return stat_dict

    def _get_interface_status(self, interface):
        cmd = self._compose_command(interface)
        output = self._run(cmd)
        rx_bytes = None
        tx_bytes = None
        rx_dropped = None
        rx_errors = None
        tx_dropped = None
        tx_errors = None
        for line in output:
            if 'RX packets' in line and ':' not in line:
                rx_bytes = int(line.split('bytes')[1].split('(')[0].strip())
            if 'TX packets' in line and ':' not in line:
                tx_bytes = int(line.split('bytes')[1].split('(')[0].strip())
            if 'RX bytes:' in line:
                rx_bytes = int(line.split('RX bytes:')[1].split(' ')[0].strip())
                tx_bytes = int(line.split('TX bytes:')[1].split(' ')[0].strip())
            if 'RX errors' in line:
                rx_errors = int(line.split('RX errors')[1].strip().split(' ')[0].strip())
                rx_dropped = int(line.split('dropped')[1].strip().split(' ')[0].strip())
            if 'TX errors' in line:
                tx_errors = int(line.split('TX errors')[1].strip().split(' ')[0].strip())
                tx_dropped = int(line.split('dropped')[1].strip().split(' ')[0].strip())
            if 'RX packets:' in line:
                rx_errors = int(line.split('errors:')[1].strip().split(' ')[0].strip())
                rx_dropped = int(line.split('dropped:')[1].strip().split(' ')[0].strip())
            if 'TX packets:' in line:
                tx_errors = int(line.split('errors:')[1].strip().split(' ')[0].strip())
                tx_dropped = int(line.split('dropped:')[1].strip().split(' ')[0].strip())
        return [rx_bytes, tx_bytes, rx_dropped, tx_dropped, rx_errors, tx_errors]

    def _compose_command(self, interface):
        cmd = "sudo ifconfig %s" % interface
        return cmd

    def _run(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
            (stdout, stderr) = proc.communicate()
            output = stdout.split("\n")
            print("cmd %s output is %s" % (cmd, output))
            result = []
            for line in output:
                if 'RX bytes' in line or 'RX packets' in line or 'TX packets' in line or 'RX errors' in line or \
                                'TX errors' in line:
                    result.append(line)
            if result is None:
                raise CmdError("failed to execute command %s, outputis %s" % (cmd, output))
            return result
        except Exception as err:
            raise CmdError("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))


def get_host_name():
        return socket.gethostname().replace("-","_")


class IfconfigStatusMon(object):
    def __init__(self):
        self.plugin_name = "interface_stat"
        self.interval = 5
        self.hostname = get_host_name()
        self.interfaces = ""
        self.verbose_logging = False
        self.account_id = None
        self.vm_type = None

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def init(self):
        self.BASE_LINE = IfconfigStatus(self.interfaces).get_all_interface_stats()

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
            elif node.key == 'Interfaces':
                self.interfaces = val
            elif node.key == "AccountId":
                self.account_id = val
            elif node.key == "VmType":
                self.vm_type = val
            else:
                collectd.warning('[plugin] %s: unknown config key: %s' % (self.plugin_name, node.key))

    def dispatch_value(self, plugin, host, type, type_instance, value):
        self.log_verbose("Dispatching value plugin=%s, host=%s, type=%s, type_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, str(value)))
        val = collectd.Values(type=type)
        val.plugin = plugin
        val.host = host
        val.type_instance = type_instance
        val.interval = self.interval
        val.values = [value]
        val.dispatch()
        self.log_verbose("Dispatched value plugin=%s, host=%s, type=%s, type_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, str(value)))

    def get_delta_dict(self, latest_dict):
        delta_dict = {}
        for key, values in latest_dict.iteritems():
            org_value = self.BASE_LINE.get(key)
            delta_rx_bytes = values[0] - org_value[0]
            delta_tx_bytes = values[1] - org_value[1]
            delta_rx_dropped = values[2] - org_value[2]
            delta_tx_dropped = values[3] - org_value[3]
            delta_rx_errors = values[4] - org_value[4]
            delta_tx_errors = values[5] - org_value[5]
            delta_dict[key] = [delta_rx_bytes, delta_tx_bytes, delta_rx_dropped, delta_tx_dropped, delta_rx_errors, delta_tx_errors]
            self.BASE_LINE[key] = values
        # {"eth0":[rx_bytes, tx_bytes, rx_dropped, tx_dropped, rx_errors, tx_errors], }
        return delta_dict

    def read_callback(self):
        try:
            self.log_verbose("plugin %s read callback called, process is: %s" % (self.plugin_name, self.interfaces))
            interface_status = IfconfigStatus(self.interfaces)
            latest_stat = interface_status.get_all_interface_stats()
            delta_stat = self.get_delta_dict(latest_stat)
            host = "%s__%s__%s" % (self.account_id, self.hostname, self.vm_type)
            for interface, value in delta_stat.iteritems():
                type_instance = interface
                # {"eth0":[rx_bytes, tx_bytes, rx_dropped, tx_dropped, rx_errors, tx_errors], }
                self.dispatch_value(self.plugin_name, host, "rx_bytes", type_instance, value[0])
                self.dispatch_value(self.plugin_name, host, "tx_bytes", type_instance, value[1])
                self.dispatch_value(self.plugin_name, host, "rx_dropped", type_instance, value[2])
                self.dispatch_value(self.plugin_name, host, "tx_dropped", type_instance, value[3])
                self.dispatch_value(self.plugin_name, host, "rx_errors", type_instance, value[4])
                self.dispatch_value(self.plugin_name, host, "tx_errors", type_instance, value[5])
        except Exception as exp:
            self.log_verbose(traceback.print_exc())
            self.log_verbose("plugin %s run into exception" % (self.plugin_name))
            self.log_verbose(exp.message)


if __name__ == '__main__':
    ifconfig_status = IfconfigStatus("eth0,eth1")
    result = ifconfig_status.get_all_interface_stats()
    print str(result)
else:
    import collectd
    ifconfig_status = IfconfigStatusMon()
    collectd.register_config(ifconfig_status.configure_callback)
    collectd.register_init(ifconfig_status.init)
    collectd.register_read(ifconfig_status.read_callback)

