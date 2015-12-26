class Connectable(object):
    def __init__(self):
        self._connectionsIn = set()
        self._connectionsOut = set()

        self.connectionAdded = Signal()
        self.connectionRemoved = Signal()
        self.sinkChanged = Signal()
        self.sourceChanged = Signal()

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
        self.sinkChanged.emit()

    @property
    def source(self):
        if self._source:
            return True
        return any([child.source for child in self._children])

    @source.setter
    def source(self, source):
        self._source = source
        self.sourceChanged.emit()

    @property
    def connectionsOut(self):
        return set(self._connectionsOut)

    @property
    def connectionsIn(self):
        # TODO: make this work with .append and .extend, etc
        return set(self._connectionsIn)

    @connectionsOut.setter
    def connectionsOut(self, newConns):
        nodesToConnect = newConns.difference(self._connectionsOut)
        nodesToDisconnect = self._connectionsOut.difference(newConns)
        for node in nodesToConnect:
            self.connectToSource(node)
        for node in nodesToDisconnect:
            self.disconnectFromSource(node)

    @connectionsIn.setter
    def connectionsIn(self, newConns):
        nodesToConnect = newConns.difference(self._connectionsIn)
        nodesToDisconnect = self._connectionsIn.difference(newConns)
        for node in nodesToConnect:
            self.connectToSink(node)
        for node in nodesToDisconnect:
            self.disconnectFromSink(node)

    @property
    def connections(self):
        allConns = self._connectionsIn.union(self._connectionsOut)
        return allConns

    @connections.setter
    def connections(self, newConns):
        curConns = self.connections
        nodesToConnect = newConns.difference(curConns)
        nodesToDisconnect = curConns.difference(newConns)
        for node in nodesToConnect:
            self.connect(node)
        for node in nodesToDisconnect:
            self.disconnect(node)

    def connect(self, param):
        if param is None:
            return
        if self.sink and param.source:
            self.connectToSource(param)
        elif self.source and param.sink:
            self.connectToSink(param)

    def connectToSource(self, param):
        if not (self.sink and param.source):
            return

        if param in self._connectionsIn:
            # This if is a little bit tricky w/ circular recursion
            # One side knows about this connection, so we don't need to
            # do anything.
            return
        self._connectionsIn.add(param)
        param.connectToSink(self)
        # Only one connect function needs the signal emission
        self.connectionAdded.emit(source=param, sink=self)

    def connectToSink(self, param):
        if not (self.source and param.sink):
            return
        if param in self._connectionsOut:
            return
        self._connectionsOut.add(param)
        param.connectToSource(self)

    def disconnectAll(self):
        self.connections = set()
