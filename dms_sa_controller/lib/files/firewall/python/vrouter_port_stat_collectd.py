# 1. use 'ovs-ofctl show br-router' to get port usage info
# 2. then use 'ovs-ofctl dump-ports br-router' to get port details like rx, tx, drop, errors
import subprocess
import socket
import traceback


class CmdError(Exception):
    pass


class VRouterPort(object):
    def get_port_traffic_details(self):
        output = self._run_port_details_cmd()
        port_info = self.get_port_info()
        #print port_info
        port_traffic_details = {}
        index = 0
        while index < len(output):
            port_number = self.__parse_port_number(output[index])
            #print port_number
            port_name = port_info.get(port_number)
            rx_info = self.__parse_traffic_details(output[index])
            tx_info = self.__parse_traffic_details(output[index+1])
            port_traffic_details[port_name] = [rx_info, tx_info]
            index += 2
        # {"cpe":[[rx_bytes, rx_drop, rx_errs], [tx_bytes, tx_drop, tx_errs]], }
        return port_traffic_details

    def __parse_port_number(self, line):
        if 'port' in line:
            return line.split(':')[0].split(' ')[-1]
        else:
            raise Exception("Cannot find port number info in line: %s" % line)

    def __parse_traffic_details(self, line):
        if 'bytes=' in line and 'drop=' in line and 'errs=' in line:
            rx_bytes = line.split('bytes=')[1].split(',')[0]
            rx_drop = line.split('drop=')[1].split(',')[0]
            rx_errs = line.split('errs=')[1].split(',')[0]
            return [rx_bytes, rx_drop, rx_errs]
        else:
            raise Exception("Cannot find traffic details info in line: %s" % line)

    def get_port_info(self):
        output = self._run_port_info_cmd()
        port_dict = {}
        for line in output:
            port_info = self._parse_port_info(line)
            port_dict[port_info[0]] = port_info[1]
        # {"1": "cpe", "2": "gw"}
        return port_dict

    def _parse_port_info(self, line):
        port_number = line.split('(')[0].strip()
        port_name = line.split('(')[1].split(')')[0].strip()
        return [port_number, port_name]

    def _run_port_info_cmd(self):
        cmd = 'sudo ovs-ofctl show br-router'
        lines = self.__run(cmd)
        result = []
        for line in lines:
            if line != '' and '(' in line and ')' in line:
                result.append(line)
        return result

    def _run_port_details_cmd(self):
        cmd = 'sudo ovs-ofctl dump-ports br-router'
        lines = self.__run(cmd)
        result = []
        for line in lines:
            if 'pkts' in line and 'bytes' in line and 'drop' in line and 'errs' in line:
                result.append(line)
        return result

    def __run(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
            (stdout, stderr) = proc.communicate()
            return stdout.split("\n")
        except Exception as err:
            raise CmdError("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))


def get_host_name():
        return socket.gethostname()


class VRouterPortMon(object):
    def __init__(self):
        self.plugin_name = "vrouter_port_stat"
        self.interval = 5
        self.hostname = get_host_name()
        self.account_id = None
        self.vm_type = None
        self.verbose_logging = False

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def init(self):
        # {"cpe":[[rx_bytes, rx_drop, rx_errs], [tx_bytes, tx_drop, tx_errs]], }
        self.BASE_LINE = VRouterPort().get_port_traffic_details()

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

    def get_delta_value(self, latest_value):
        # {"cpe":[[rx_bytes, rx_drop, rx_errs], [tx_bytes, tx_drop, tx_errs]], }
        delta_dict = {}
        for key, values in latest_value.iteritems():
            org_value = self.BASE_LINE.get(key)
            rx_bytes = int(values[0][0]) - int(org_value[0][0])
            rx_drop = int(values[0][1]) - int(org_value[0][1])
            rx_errs = int(values[0][2]) - int(org_value[0][2])

            tx_bytes = int(values[1][0]) - int(org_value[1][0])
            tx_drop = int(values[1][1]) - int(org_value[1][1])
            tx_errs = int(values[1][2]) - int(org_value[1][2])

            rx_values = [rx_bytes, rx_drop, rx_errs]
            tx_values = [tx_bytes, tx_drop, tx_errs]

            delta_dict[key] = [rx_values, tx_values]
            self.BASE_LINE[key] = values
        # {"cpe":[[rx_bytes, rx_drop, rx_errs], [tx_bytes, tx_drop, tx_errs]], }
        return delta_dict

    def dispatch_value(self, plugin, host, type, type_instance, value):
        self.log_verbose("Dispatching value plugin=%s, host=%s, type=%s, type_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, str(value)))
        val = collectd.Values(type=type)
        val.plugin = plugin
        val.host = host
        val.type_instance = type_instance
        val.values = [value]
        val.dispatch()
        self.log_verbose("Dispatched value plugin=%s, host=%s, type=%s, type_instance=%s, value=%s" %
                         (plugin, host, type, type_instance, str(value)))

    def read_callback(self):
        try:
            self.log_verbose("plugin %s read callback called" % self.plugin_name)
            host = "%s__%s__%s" % (self.account_id, self.hostname, self.vm_type)
            vrouter_port_stat = VRouterPort()
            latest_stat = vrouter_port_stat.get_port_traffic_details()
            statuses = self.get_delta_value(latest_stat)
            # {"cpe":[[rx_bytes, rx_drop, rx_errs], [tx_bytes, tx_drop, tx_errs]], }
            for key, value in statuses.iteritems():
                type_instance = key
                self.dispatch_value(self.plugin_name, host, 'rx_bytes', type_instance, value[0][0])
                self.dispatch_value(self.plugin_name, host, 'rx_drop', type_instance, value[0][1])
                self.dispatch_value(self.plugin_name, host, 'rx_errs', type_instance, value[0][2])

                self.dispatch_value(self.plugin_name, host, 'tx_bytes', type_instance, value[1][0])
                self.dispatch_value(self.plugin_name, host, 'tx_drop', type_instance, value[1][1])
                self.dispatch_value(self.plugin_name, host, 'tx_errs', type_instance, value[1][2])
        except Exception as exp:
            self.log_verbose(traceback.print_exc())
            self.log_verbose(exp.message)


if __name__ == '__main__':
    vrouter = VRouterPort()
    result = vrouter.get_port_traffic_details()
    print '-------'
    print result
else:
    import collectd
    vrouter_port_mon = VRouterPortMon()
    collectd.register_config(vrouter_port_mon.configure_callback)
    collectd.register_init(vrouter_port_mon.init)
    collectd.register_read(vrouter_port_mon.read_callback)