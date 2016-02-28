import os
from kafka import KafkaConsumer
from ConfigParser import SafeConfigParser
import avro.io
import avro.schema
import io
import json
from models import ObjectFactory
from connects import ConnectFactory
from util import logger


avro_schema = """
    {"namespace": "com.dadycloud.sa",
    "type": "record",
    "name": "event",
    "fields": [
                 {"name": "timestamp", "type": "long"},
                 {"name": "src",       "type": "string"},
                 {"name": "host_ip",   "type": "string"},
                 {"name": "rawdata",   "type": "bytes"}
            ]
            }
         """



class KafkaCollector():
    def __init__(self):
        self.app_home = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.app_home)
        self.config = SafeConfigParser()
        config_file = os.path.join(self.app_home,"config.conf")
        self.config.read(config_file)
        self.kafka_host = self.config.get("Kafka","kafka_broker")
        self.kafka_topic = self.config.get("Kafka","kafka_topic")
        self.kafka_group = self.config.get("Kafka","kafka_group")
        self.consumer = KafkaConsumer(self.kafka_topic,self.kafka_group,bootstrap_servers=[self.kafka_host])
        self.schema = avro.schema.parse(avro_schema)

    def run(self):
        client = ConnectFactory().getConnect("redis",self.config)
        for msg in self.consumer:
            kafkamsg = self._decodemsg(msg)
            try:
                logger.info("message handling(%s)" % kafkamsg)
                jsondata = json.loads(kafkamsg['rawdata'])
                ObjectFactory.fromjson(jsondata["message"]).execute(client)

            except:
                logger.error("message execute error(%s)" % jsondata)



    def _decodemsg(self,msg):
        value = bytearray(msg.value)
        bytes_reader = io.BytesIO(value[5:])
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.schema)
        message = reader.read(decoder)
        return message

if __name__ == '__main__':
    kafka_runner = KafkaCollector()
    kafka_runner.run()
