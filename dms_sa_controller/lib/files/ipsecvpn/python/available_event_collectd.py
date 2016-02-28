#!/usr/bin/env python
#coding=utf-8

import subprocess
import socket
import time
import avro
import avro.schema
import io
import traceback
from avro.io import DatumWriter
from kafka.client import KafkaClient
from kafka.producer import SimpleProducer


class FPingError(Exception):
    pass


class CmdError(FPingError):
    pass


class FPing(object):
    def __init__(self, path='/usr/bin/fping', interval=10, src_host='localhost', dst_hosts=[]):
        self.path = path
        self.interval = interval
        self.src_host = src_host
        self.dst_hosts = dst_hosts

    def _compose_cmd_line(self):
        cmd = ['sudo', self.path, '-e']
        for host in self.dst_hosts:
            cmd.append(host)
        return ' '.join(cmd)

    def _run(self):
        cmd = self._compose_cmd_line()
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
        (stdout, stderr) = proc.communicate()
        if stdout is None or stdout == '':
            raise CmdError('Command: %s has no output.' % cmd)
        return stdout

    def get_fping_result(self):
        result = []
        output = self._run()
        lines = output.split('\n')
        for line in lines:
            #centos will output extra ICMP Network Unreachable xxx info
            if 'ICMP Network' in line or line == '':
                continue
            result.append(line)

        return result

    def get_elapsed_time(self):
        result = []
        output = self._run()
        elapsed_time_data = output.split('\n')
        for data in elapsed_time_data:
            if data != '':
                dst_host, elapsed_time = self._parse_elapsed_time(data)
                # dst_host = self.src_host + "_" + dst_host
                dst_host = dst_host
                print("host: %s -> time: %f" % (dst_host, elapsed_time))
                result.append([dst_host, elapsed_time])
        return result

    def _parse_elapsed_time(self, line):
        if 'unreachable' in line:
            items = line.split(' ')
            dst_host = items[0].replace("-",".")
            elapsed_time = -1.0
        else:
            items = line.split('(')
            dst_host = items[0].split(' ')[0]
            elapsed_time = float(items[1].replace(' ms)', ''))
        return (dst_host, elapsed_time)


def get_host_name():
    return socket.gethostname().replace("-", "_")


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


def compose_data(timestamp, src_vmtype, host_ip, account_id, dest_ip):
    writer = DatumWriter(get_schema())
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    message = '{"eventName": "Neighbour_Unreachable", "accountId":"%s", "destIp":"%s"}' \
              % (account_id, dest_ip)
    raw_data = bytes(message)
    writer.write({"timestamp": timestamp, "src": src_vmtype, "host_ip": host_ip, "rawdata":raw_data}, encoder)
    raw_bytes = bytes_writer.getvalue()
    return raw_bytes


class FPingMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-fping-python'
        self.fping_path = '/usr/bin/fping'
        self.src_host = get_host_name()
        self.neighbours = []
        self.fping_interval = 10
        self.vm_type = None
        self.account_id = None
        self.kafka_client = None
        self.kafka_topic = None
        self.producer = None
        self.verbose_logging = False

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s ' % (self.plugin_name, msg))

    @staticmethod
    def handle_special_letter(line):
        line = line.strip()
        if line.endswith(','):
            line = line[:-1]
        return line


    def configure_callback(self, conf):
        for node in conf.children:
            val = str(node.values[0])

            if node.key == 'Path':
                self.fping_path = val
            elif node.key == 'Interval':
                self.fping_interval = float(val)
            elif node.key == 'PluginName':
                self.plugin_name = val
            elif node.key == 'Neighbours':
                self.neighbours = self.handle_special_letter(val).split(',')
            elif node.key == "KafkaClient":
                self.kafka_client = val
            elif node.key == "KafkaTopic":
                self.kafka_topic = val
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            elif node.key == 'AccountId':
                self.account_id = val
            elif node.key == "VmType":
                self.vm_type = val
            elif node.key == "HostName":
                self.src_host = val
            else:
                collectd.warning('%s plugin: Unknown config key: %s.' % (self.plugin_name, node.key))

        self.log_verbose('Configured with plugin_name=%s, fping_path=%s, interval=%d, neighbours=%s, '
                         'verbose_logging=%s, kafka_client=%s, kafka_topic=%s, account_id=%s' %
                         (self.plugin_name, self.fping_path, self.fping_interval, str(self.neighbours),
                          str(self.verbose_logging), self.kafka_client, self.kafka_topic, self.account_id))

    def init(self):
        self.producer = create_kafka_producer(self.kafka_client)
        self.log_verbose(str(self.producer.async))

    def read_callback(self):
        try:
            self.log_verbose('Read callback called')
            fping = FPing(path=self.fping_path, interval=self.fping_interval, src_host=self.src_host,
                          dst_hosts=self.neighbours)
            data = fping.get_fping_result()
            self.log_verbose(data)
            self.log_verbose(self.producer.async)
            for each_data in data:
                if each_data != '':
                    if 'unreachable' in each_data:
                        dest_ip = each_data.split(' ')[0]
                        timestamp = long(time.time())
                        data = compose_data(timestamp, self.vm_type, self.src_host, self.account_id, dest_ip)
                        try:
                            self.producer.send_messages(self.kafka_topic, data)
                        except:
                            self.producer = create_kafka_producer(self.kafka_client)
                            self.producer.send_messages(self.kafka_topic, data)
        except Exception as exp:
            self.log_verbose("run into exception")
            self.log_verbose(exp.message)
            self.log_verbose(exp.args)
            raise Exception("Failed to send msg to kafka: %s\n%s" % (exp.message, traceback.print_exc()))


if __name__ == '__main__':
    # fping = FPing(dst_hosts=['8.8.8.8', '1.1.1.1'])
    # result = fping.get_elapsed_time()
    data = compose_data(long(time.time()), "firewall", "src_host", "account1234", "8.8.8.8")
    producer = create_kafka_producer("172.17.8.113:9092")
    producer.send_messages('dms-event',b'this is for test')
    print 'aa'
else:
    import collectd
    fping_mon = FPingMon()
    collectd.register_config(fping_mon.configure_callback)
    collectd.register_init(fping_mon.init)
    collectd.register_read(fping_mon.read_callback)

