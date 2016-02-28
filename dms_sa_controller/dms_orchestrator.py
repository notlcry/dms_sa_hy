import os

from ConfigParser import SafeConfigParser

from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from yapsy.PluginManager import  PluginManagerSingleton
from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
from yapsy.VersionedPluginManager import VersionedPluginManager
from lib.base.inputbase import InputBase
from lib.base.handlebase import HandleBase
from lib.services.servicecontext import ServiceContext
from Queue import Queue
from apscheduler.schedulers.background import BackgroundScheduler
from rundeck.client import  Rundeck
from lib.dsoSynczoo.full_sync_accounts_tran import full_sync

class DmsOrchestrator:

    ORCH_SECTION = "Orchestrator"

    def __init__(self):
        self.app_home = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.app_home)

    def _configInitialize(self):
        self.config = SafeConfigParser()
        config_file = os.path.join(self.app_home,"orchestrator.conf")
        print config_file
        self.config.read(config_file)
        local_path = self.config.get("File","local_temp_path")
        if not os.path.exists(local_path):
             os.makedirs(local_path)


    def _mangerInitialize(self):
        PluginManagerSingleton.setBehaviour([MultiprocessPluginManager,
                                         ConfigurablePluginManager,
                                         VersionedPluginManager])
        self.manager = PluginManagerSingleton.get()


    def initializeScheduler(self):
        scheduler = BackgroundScheduler()
        connect_url = self.config.get(self.ORCH_SECTION,"sched_connect_url")
        scheduler.add_jobstore('sqlalchemy',url=connect_url)
        scheduler.start()
        return scheduler

    def _serviceInitialize(self):
        ctx = ServiceContext()
        queue = Queue()
        ctx.registerQueueService(queue)
        ctx.registerSchedService(self.initializeScheduler())
        ctx.registerConfigService(self.config)
        server = self.config.get("Rundeck","rundeck_server")
        apitoken = self.config.get("Rundeck","api_token")
        rdclient = Rundeck(server=server,api_token=apitoken)
        ctx.registerRdClient(rdclient)

    def _pluginInitialize(self):
        self.manager.setPluginPlaces(["lib/plugins"])
        self.manager.setConfigParser(self.config,None)
        self.manager.setCategoriesFilter({'Handler':HandleBase,"Input":InputBase})
        self.manager.collectPlugins()

    def _watiInputDone(self):
        plugins = self.manager.getPluginsOfCategory('Input')
        map(lambda plugin:plugin.plugin_object.proc.join(),plugins)

    def _inventorySync(self):
        zk_address = self.config.get("Inventory","zk_address")
        full_sync(zk_address)

    def start(self):
        self._configInitialize()
        self._mangerInitialize()
        self._serviceInitialize()
        self._inventorySync();
        self._pluginInitialize()
        #self._watiInputDone()
        import time
        while True:
           time.sleep(30)


if __name__ == "__main__":
    from lib.utils import Logger
    Logger.basicConfig()
    app = DmsOrchestrator()
    app.start()
