from yapsy.IMultiprocessChildPlugin import IMultiprocessChildPlugin
from yapsy.PluginManager import PluginManagerSingleton
import base
class InputBase(base.PluginBase):
    def getCategory(self):
        return "Input"




