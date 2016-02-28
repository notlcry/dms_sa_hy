def singleton(cls):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return _singleton

from pydispatch import dispatcher

def register(func):
    name = func.__name__
    if name.startswith("handle"):
        event = name[6:].upper()
        dispatcher.connect(func,signal=event,sender=dispatcher.Any)
    def adapter(*args,**kwargs):
         return func(*args,**kwargs)
    return  adapter


from log import Logger
logger = Logger()










