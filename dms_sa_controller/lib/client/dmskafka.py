from kafka import KafkaClient,SimpleProducer
from ..utils import singleton,logger
from .. services.servicecontext import ServiceContext
import avro.io
import avro.schema
import io
from ..utils.constants import avro_schema
import json
@singleton
class DmsKafkaClient(object):
    def __init__(self):
        config = ServiceContext().getConfigService()
        broker_list = config.get("Message","kafka_producer")
        kafka = KafkaClient(broker_list)
        self.producer = SimpleProducer(kafka)
        self.zabbix_alert = config.get("Message","zabbix_alert_topic")

    def sendPackageTimeout(self,accountId):
        message = {
            "accountId":accountId,
            "host":None,
            "item":None,
            "severity": "ERROR",
            "description": "account %s workflow timeout" % accountId
        }
        all = {
            "timestamp": 1L,
            "src": "rundeck",
            "host_ip": "10.74.113.101",
            "rawdata":json.dumps(message)
        }
        schema = avro.schema.parse(avro_schema)
        writer = avro.io.DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(all,encoder)
        try:
            self.producer.send_messages(b"%s"%self.zabbix_alert,bytes_writer.getvalue())
            logger.info("send to zabbix sa successfully")
        except:
            logger.error("occur error when send package timeout message to zabbix alert topic")