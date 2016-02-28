from kafka import KafkaClient, SimpleProducer
from ..utils import singleton, logger
from ..services.servicecontext import ServiceContext
import avro.io
import avro.schema
import io
from ..utils.constants import avro_schema
import json


@singleton
class InventoryKafkaClient(object):
    def __init__(self):
        config = ServiceContext().getConfigService()
        broker_list = config.get("Message", "kafka_producer")
        kafka = KafkaClient(broker_list)
        self.producer = SimpleProducer(kafka)
        # self.inventory_notify = config.get("Kafka", "kafka_topic")
        self.inventory_notify = 'dms.log.inventory'

    def send_inventory(self, account_id, module, operation, result, data):
        message = {
            "accountId": account_id,
            "module": module,
            "operation": operation,
            "result": result,
            "data": data
        }
        all = {
            "timestamp": 1L,
            "src": "sa_inventory",
            "host_ip": "10.74.113.101",
            "rawdata": json.dumps(message)
        }
        schema = avro.schema.parse(avro_schema)
        writer = avro.io.DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(all, encoder)
        try:
            self.producer.send_messages(b"%s" % self.inventory_notify, bytes_writer.getvalue())
            logger.info("send to redis successfully")
        except Exception as exp:
            logger.error("occur error when send package inventory message to "
                         "sa inventory(dms.log.inventory) topic" + exp.message)

    def send_create(self, account_id, module, data):
        self.send_inventory(account_id, module, "create", "success", data)
