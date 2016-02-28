#!/usr/bin/env python
#coding=utf-8

import socket
import subprocess
import traceback


class CmdError(Exception):
    pass


class TopNProcs(object):
    def __init__(self, top_n):
        self.top_n = top_n

    def get_top_n_procs_by_cpu(self):
        cmd = self._compose_top_n_proc_by_cpu()
        result = self._run(cmd)
        top_n_procs = result[1:]
        return top_n_procs

    def get_top_n_procs_by_memory(self):
        cmd = self._compose_top_n_proc_by_memory()
        result = self._run(cmd)
        return result

    def _compose_top_n_proc_by_cpu(self):
        cmd = "ps aux | sort -rk 3,3 | head -n %s | awk '{print $11}'" % (self.top_n + 1)
        return cmd

    def _compose_top_n_proc_by_memory(self):
        cmd = "ps aux | sort -nk +4 | tail -n %s | awk '{print $11}'" % self.top_n
        return cmd

    def _run(self, cmd):
        try:
            result = []
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
            (stdout, stderr) = proc.communicate()
            output = stdout.split("\n")
            for line in output:
                if line == '':
                    continue
                result.append(line)
            print("cmd %s output is %s" % (cmd, output))
            return result
        except Exception as err:
            raise CmdError("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))


def get_host_name():
        return socket.gethostname().replace("-","_")


class TopNProcsMon(object):
    def __init__(self):
        self.plugin_name = "top_n_proc_stat"
        self.interval = 30
        self.hostname = None
        self.account_id = None
        self.vm_type = None
        self.top_n = None
        self.verbose_logging = False

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def configure_callback(self, conf):
        for node in conf.children:
            val = str(node.values[0])

            if node.key == "HostName":
                self.hostname = val
            elif node.key == "AccountId":
                self.account_id = val
            elif node.key == "VmType":
                self.vm_type = val
            elif node.key == 'TOP_N':
                self.top_n = int(float(val))
            elif node.key == 'Interval':
                self.interval = int(float(val))
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            elif node.key == 'PluginName':
                self.plugin_name = val
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

    def read_callback(self):
        try:
            top_n_proc = TopNProcs(self.top_n)
            cpu_top_n = top_n_proc.get_top_n_procs_by_cpu()
            memory_top_n = top_n_proc.get_top_n_procs_by_memory()

            host = "%s__%s__%s" % (self.account_id, self.hostname, self.vm_type)
            index = 1
            for item in cpu_top_n:
                type = 'by_cpu'
                type_instance = item
                value = index
                self.dispatch_value(self.plugin_name, host, type, type_instance, value)
                index += 1

            index = 1
            for item in memory_top_n:
                type = 'by_memory'
                type_instance = item
                value = index
                self.dispatch_value(self.plugin_name, host, type, type_instance, value)
                index += 1

        except Exception as exp:
            self.log_verbose(traceback.print_exc())
            self.log_verbose("plugin %s run into exception" % (self.plugin_name))
            self.log_verbose(exp.message)


if __name__ == '__main__':
    # process_status = ProcessStatus("pyth[on], /usr/bin/ss[hd], ja[va]")
    process_status = TopNProcs(5)
    result = process_status.get_top_n_procs_by_cpu()
    print '*******by cpu********'
    print str(result)
    print '\n'
    result = process_status.get_top_n_procs_by_memory()
    print '*******by memory********'
    print str(result)
else:
    import collectd
    process_status_mon = TopNProcsMon()
    collectd.register_config(process_status_mon.configure_callback)
    collectd.register_read(process_status_mon.read_callback)

