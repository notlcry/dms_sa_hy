from common import singleton,Config
from rundeck.client import Rundeck
@singleton
class RundeckNode(object):
    def __init__(self):
        url = Config().getRundeckUrl()
        token = Config().getRundeckToken()
        self.client = Rundeck(server=url,api_token=token)

