class Connectable(object):
    def __init__(self):
        self._connections_in = set()
        self._connections_out = set()

        self.connection_added = Signal()
        self.connection_removed = Signal()
        self.sink_changed = Signal()
        self.source_changed = Signal()

        self._sink = False
        self._source = False

    @property
    def sink(self):
        if self._sink:
            return True
        return any([child.sink for child in self._children])

    @sink.setter
    def sink(self, sink):
        self._sink = sink
        self.sink_changed.emit()

    @property
    def source(self):
        if self._source:
            return True
        return any([child.source for child in self._children])

    @source.setter
    def source(self, source):
        self._source = source
        self.source_changed.emit()

    @property
    def connections_out(self):
        return set(self._connections_out)

    @property
    def connections_in(self):
        # TODO: make this work with .append and .extend, etc
        return set(self._connections_in)

    @connections_out.setter
    def connections_out(self, new_conns):
        nodes_to_connect = new_conns.difference(self._connections_out)
        nodes_to_disconnect = self._connections_out.difference(new_conns)
        for node in nodes_to_connect:
            self.connect_to_source(node)
        for node in nodes_to_disconnect:
            self.disconnectFromSource(node)

    @connections_in.setter
    def connections_in(self, new_conns):
        nodes_to_connect = new_conns.difference(self._connections_in)
        nodes_to_disconnect = self._connections_in.difference(new_conns)
        for node in nodes_to_connect:
            self.connect_to_sink(node)
        for node in nodes_to_disconnect:
            self.disconnectFromSink(node)

    @property
    def connections(self):
        all_conns = self._connections_in.union(self._connections_out)
        return all_conns

    @connections.setter
    def connections(self, new_conns):
        cur_conns = self.connections
        nodes_to_connect = new_conns.difference(cur_conns)
        nodes_to_disconnect = cur_conns.difference(new_conns)
        for node in nodes_to_connect:
            self.connect(node)
        for node in nodes_to_disconnect:
            self.disconnect(node)

    def connect(self, param):
        if param is None:
            return
        if self.sink and param.source:
            self.connect_to_source(param)
        elif self.source and param.sink:
            self.connect_to_sink(param)

    def connect_to_source(self, param):
        if not (self.sink and param.source):
            return

        if param in self._connections_in:
            # This if is a little bit tricky w/ circular recursion
            # One side knows about this connection, so we don't need to
            # do anything.
            return
        self._connections_in.add(param)
        param.connect_to_sink(self)
        # Only one connect function needs the signal emission
        self.connection_added.emit(source=param, sink=self)

    def connect_to_sink(self, param):
        if not (self.source and param.sink):
            return
        if param in self._connections_out:
            return
        self._connections_out.add(param)
        param.connect_to_source(self)

    def disconnectAll(self):
        self.connections = set()
