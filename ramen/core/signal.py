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
        for slot, (conn_args, conn_kwargs) in self._slots.items():
            full_args = list(conn_args)
            full_args.extend(args)

            full_kwargs = dict(conn_kwargs)
            full_kwargs.update(kwargs)
            argspec = inspect.getargspec(slot)
            if not argspec.keywords:
                for key in list(full_kwargs.keys()):
                    if key not in argspec.args:
                        del full_kwargs[key]

            slot(*full_args, **full_kwargs)

    def connect(self, slot, *slot_args, **slot_kwargs):
        self._slots[slot] = (slot_args, slot_kwargs)

    def disconnect(self, slot):
        if slot in self._slots:
            del self._slots[slot]
        else:
            print('Warning: Could not disconnect %s from %s' % (slot, self))
