import inspect


class Signal(object):
    '''Small implementation of signals/slots with optional arguments'''
    def __init__(self):
        # _slots is a dictionary of:
        # Key: function to call when this signal is emitted.
        # Value: tuple of args and kwargs specified at connection time.
        # The connection-time args are useful for specifying default
        # arguments that emit may or may not specify (most commonly not).
        # A function can only be connected to a Signal once.
        self._slots = {}

    def emit(self, *args, **kwargs):
        for slot, (connArgs, connKwargs) in self._slots.items():
            fullArgs = list(connArgs)
            fullArgs.extend(args)

            fullKwargs = dict(connKwargs)
            fullKwargs.update(kwargs)
            argspec = inspect.getargspec(slot)
            if not argspec.keywords:
                for key in list(fullKwargs.keys()):
                    if key not in argspec.args:
                        del fullKwargs[key]

            slot(*fullArgs, **fullKwargs)

    def connect(self, slot, *slotArgs, **slotKwargs):
        self._slots[slot] = (slotArgs, slotKwargs)

    def disconnect(self, slot):
        if slot in self._slots:
            del self._slots[slot]
        else:
            print('Warning: Could not disconnect %s from %s' % (slot, self))
