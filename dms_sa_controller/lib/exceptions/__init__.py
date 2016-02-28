class DMSError(Exception):
    """
    Base class for exceptions
    """
    pass

class InputError(DMSError):
    def __init__(self,reason):
        self.reason = reason
    def __str__(self):
        return "input format is invalid, %s" % self.reason
