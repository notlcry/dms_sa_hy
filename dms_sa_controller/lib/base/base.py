import IMultithreadChildPlugin
from yapsy.PluginManager import PluginManagerSingleton

class PluginBase(IMultithreadChildPlugin.IMultithreadChildPlugin):
    def getCategory(self):
        return None

    def getPluginName(self):
        return None
