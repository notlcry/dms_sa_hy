from lib.base.inputbase import InputBase
from lib.services.servicecontext import ServiceContext
from lib.events import EventFactory
import json
from lib.utils import Logger
from lib.exceptions import *
from kafka import KafkaConsumer

class EventCollector(InputBase,Logger):

    def run(self):
        ctx = ServiceContext()
        queue = ctx.getQueueService()
        config = ctx.getConfigService()

        constructor="KafkaConsumer(%s,group_id=%s,bootstrap_servers=%s)"
        topics = config.get("Input Plugin: event_collector","event_topic")
        group_id = config.get("Input Plugin: event_collector","event_groupid")
        bootstrap_server = config.get("Message","kafka_broker")
        str = constructor % (topics,group_id,bootstrap_server)
        self.consumer = eval(str)

        for msg in self.consumer:
#            value = bytearray(msg.value)
            topic = msg.topic
            try:
                jsondata = json.loads(msg.value)
                eventType = jsondata["eventName"]
                jsondata['topic'] = topic
                queue.put(EventFactory.getEvent(eventType,jsondata))
            except IndexError,e:
                self.error(e)








