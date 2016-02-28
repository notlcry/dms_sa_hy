from lib.base.inputbase import InputBase
from lib.services.servicecontext import ServiceContext
import avro.io
import avro.schema
import io
from lib.events import EventFactory
import json
from lib.utils import Logger
from lib.exceptions import *
from kafka import KafkaConsumer
from lib.utils.constants import avro_schema
class KafkaCollector(InputBase,Logger):

    def run(self):
        ctx = ServiceContext()
        config = ctx.getConfigService()
        queue = ctx.getQueueService()
        self.schema = avro.schema.parse(avro_schema)

        constructor="KafkaConsumer(%s,group_id=%s,bootstrap_servers=%s)"
        topics = config.get("Input Plugin: kafka_collector","kafka_topics")
        group_id = config.get("Input Plugin: kafka_collector","kafka_groupid")
        bootstrap_server = config.get("Message","kafka_broker")
        str = constructor % (topics,group_id,bootstrap_server)
        self.consumer = eval(str)

        for msg in self.consumer:
            value = bytearray(msg.value)
            topic = msg.topic
            bytes_reader = io.BytesIO(value[5:])
            decoder = avro.io.BinaryDecoder(bytes_reader)
            reader = avro.io.DatumReader(self.schema)
            kafkamsg = reader.read(decoder)
            try:
                jsondata = json.loads(kafkamsg['rawdata'])
                eventType = jsondata["eventName"]
                jsondata['topic'] = topic
                queue.put(EventFactory.getEvent(eventType,jsondata))
            except InputError,e:
                self.error(str(e))
            except:
                self.error("message format is invalid(%s)" % jsondata)



    def _decodemsg(self,msg):
        value = bytearray(msg.value)
        bytes_reader = io.BytesIO(value[5:])
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.schema)
        message = reader.read(decoder)
        return message

