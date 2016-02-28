#!/usr/bin/env python
#coding=utf-8

import socket
import subprocess
import time
import traceback
import avro
import avro.schema
import io
from avro.io import DatumWriter
from kafka.client import KafkaClient
from kafka.producer import SimpleProducer


class CmdError(Exception):
    pass


class ProcessStatus(object):
    def __init__(self, processes):
        self.processes = processes

    def get_procs_status(self):
        status = {}
        procs = self.processes.split(',')
        for proc in procs:
            proc = proc.strip()
            command = self._compose_command(proc)
            result = self._run(command)
            if len(result) == 0:
                status[proc] = 0
            else:
                status[proc] = 1
        return status

    def _compose_command(self, proc):
        cmd = "sudo ps -elf | grep %s | awk '{print $15}'" % (proc)
        return cmd

    def _run(self, cmd):
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
            (stdout, stderr) = proc.communicate()
            output = stdout.split("\n")
            print("cmd %s output is %s" % (cmd, output))
            result = []
            for line in output:
                line = line.strip()
                if line == '' or line == 'grep' or line == '/bin/sh':
                    continue
                else:
                    result.append(line)
            return result
        except Exception as err:
            raise CmdError("failed to execute command: %s, reason: %s" % (' '.join(cmd), err.message))


def get_host_name():
        return socket.gethostname().replace("-","_")


def create_kafka_producer(kafka_host_port):
    try:
        client = KafkaClient(kafka_host_port)
        producer = SimpleProducer(client, async=True)
        return producer
    except Exception as excp:
        raise Exception("Failed to set up kafka producer: %s" % excp.message)


def get_schema():
    schema_string = """{"namespace": "com.dadycloud.sa",
              "type": "record",
              "name": "event",
              "fields":[
                  {"name": "timestamp", "type":"long"},
                  {"name": "src", "type": "string"},
                  {"name": "host_ip", "type": "string"},
                  {"name": "rawdata", "type":"bytes"}
              ]

    }"""
    schema = avro.schema.parse(schema_string)
    return schema


def compose_data(timestamp, src_vmtype, host_ip, account_id, proc_name):
    writer = DatumWriter(get_schema())
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    message = '{"eventName": "Process_Down", "accountId":"%s", "ProcName":"%s"}' \
              % (account_id, proc_name)
    raw_data = bytes(message)
    writer.write({"timestamp": timestamp, "src": src_vmtype, "host_ip": host_ip, "rawdata":raw_data}, encoder)
    raw_bytes = bytes_writer.getvalue()
    return raw_bytes


class ProcessStatusMon(object):
    def __init__(self):
        self.plugin_name = "collectd_process_status"
        self.interval = 10
        self.hostname = get_host_name()
        self.processes = ""
        self.verbose_logging = True
        self.kafka_client = None
        self.kafka_topic = None
        self.account_id = None
        self.vm_type = None
        self.producer = None

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def init(self):
        self.producer = create_kafka_producer(self.kafka_client)
        self.log_verbose(str(self.producer.async))

    def configure_callback(self, conf):
        for node in conf.children:
            val = str(node.values[0])

            if node.key == 'Interval':
                self.interval = int(float(val))
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            elif node.key == 'PluginName':
                self.plugin_name = val
            elif node.key == 'Processes':
                self.processes = val
            elif node.key == "KafkaClient":
                self.kafka_client = val
            elif node.key == "KafkaTopic":
                self.kafka_topic = val
            elif node.key == "AccountId":
                self.account_id = val
            elif node.key == "VmType":
                self.vm_type = val
            elif node.key == "HostName":
                self.hostname = val
            else:
                collectd.warning('%s plugin: Unknown config key: %s.' % (self.plugin_name, node.key))
        self.log_verbose('Configured with plugin_name=%s, Hostname=%s, interval=%s, processes=%s, '
                         'verbose_logging=%s, kafka_client=%s, kafka_topic=%s, account_id=%s, vm_type=%s' %
                         (self.plugin_name, self.hostname, self.interval,self.processes,self.verbose_logging,
                          self.kafka_client, self.kafka_topic, self.account_id, self.vm_type))

    def read_callback(self):
        try:
            self.log_verbose("plugin %s read callback called, process is: %s" % (self.plugin_name, self.processes))
            process_status = ProcessStatus(self.processes)
            statuses = process_status.get_procs_status()
            for key, value in statuses.iteritems():
                if value == 0:
                    timestamp = long(time.time())
                    proc_name = key
                    data = compose_data(timestamp, self.vm_type, self.hostname, self.account_id, proc_name)
                    try:
                        self.producer.send_messages(self.kafka_topic, data)
                    except:
                        self.producer = create_kafka_producer(self.kafka_client)
                        self.producer.send_messages(self.kafka_topic, data)
        except Exception as exp:
            self.log_verbose(traceback.print_exc())
            self.log_verbose("plugin %s run into exception" % (self.plugin_name))
            self.log_verbose(exp.message)
            raise Exception("Failed to send msg to kafka: %s\n%s" % (exp.message, traceback.print_exc()))

    def _escape_proc_name(self, proc):
        if str(proc) == '0':
            return '0'
        return proc.replace('[', '').replace(']', '').replace('/', '.').replace("-", "_")


if __name__ == '__main__':
    # process_status = ProcessStatus("pyth[on], /usr/bin/ss[hd], ja[va]")
    producer = create_kafka_producer("172.17.8.113:9092")
    producer.send_messages('dms-event',b'this is for test process')
    print 'aa'
else:
    import collectd
    process_status_mon = ProcessStatusMon()
    collectd.register_config(process_status_mon.configure_callback)
    collectd.register_init(process_status_mon.init)
    collectd.register_read(process_status_mon.read_callback)

