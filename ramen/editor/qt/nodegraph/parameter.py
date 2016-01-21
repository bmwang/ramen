from PyQt4 import QtGui, QtCore
from ramen.editor.qt.nodegraph.nodegraphscene import NodegraphScene
from ramen.editor.qt.nodegraph.connection import Connection
from ramen.signal import Signal


class Parameter(QtGui.QGraphicsItem):
    def __init__(self, nodegraph, ramenParameter, *args, **kwargs):
        kwargs['scene'] = nodegraph.getNodeUI(ramenParameter.node).scene()
        super(Parameter, self).__init__(*args, **kwargs)
        self._nodegraph = nodegraph
        self._ramenParameter = ramenParameter
        self._label = QtGui.QGraphicsTextItem(self)

        self._connectionsOut = {}

        # TODO consider wiring the node's updatedGeo to this
        self.updatedGeo = Signal()

        self.registerRamenCallbacks()
        self.syncConnections()
        self.updateGeo()

    @property
    def nodegraph(self):
        return self._nodegraph

    @property
    def ramenParameter(self):
        return self._ramenParameter

    def registerRamenCallbacks(self):
        self.ramenParameter.connection_added.connect(
            self._connectionAddedCallback)
        self.ramenParameter.connection_removed.connect(
            self._connectionRemovedCallback)
        self.ramenParameter.source_changed.connect(self.updateGeo)
        self.ramenParameter.sink_changed.connect(self.updateGeo)

    def deregisterRamenCallbacks(self):
        self.ramenParameter.connection_added.disconnect(
            self._connectionAddedCallback)
        self.ramenParameter.connection_removed.disconnect(
            self._connectionRemovedCallback)
        self.ramenParameter.source_changed.disconnect(self.updateGeo)
        self.ramenParameter.sink_changed.disconnect(self.updateGeo)

    def _connectionAddedCallback(self, source, sink):
        # Only create the connection if we're the source
        # (prevent double-creating the connection)
        if source == self.ramenParameter:
            return self._addConnectionOut(sink)

    def _connectionRemovedCallback(self, source, sink):
        if source == self.ramenParameter:
            return self._removeConnectionOut(sink)

    def updateGeo(self):
        nodeUI = self.nodegraph.getNodeUI(self.ramenParameter.node)

        boundingRect = QtCore.QRectF()
        self._label.setDefaultTextColor(QtGui.QColor(255, 255, 255, 150))
        if self.ramenParameter.parent is None:
            self._label.setPlainText('')
        else:
            labelText = self.ramenParameter.label
            # XXX quick way to show sources/sinks; unicode for arrow
            if self.ramenParameter.sink:
                labelText = u'\u25b6 ' + labelText
            if self.ramenParameter.source:
                labelText = labelText + u' \u25b6'
            self._label.setPlainText(labelText)
            boundingRect |= self._label.boundingRect().translated(
                    self._label.pos())
        for childParameter in self.ramenParameter.children:
            childParameterUI = nodeUI.getParameterUI(childParameter)
            childParameterUI.setPos(0, boundingRect.height())
            boundingRect |= childParameterUI.boundingRect().translated(
                    childParameterUI.pos())
        self.updatedGeo.emit()

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, *args):
        pass

    def syncConnections(self):
        connectionsOut = set(self.ramenParameter.connections_out)
        knownConnectionsOut = set(self._connectionsOut.keys())

        connectionsOutToRemove = knownConnectionsOut.difference(connectionsOut)
        connectionsOutToAdd = connectionsOut.difference(knownConnectionsOut)

        for sinkParam in connectionsOutToRemove:
            self._removeConnectionOut(sinkParam)
        for sinkParam in connectionsOutToAdd:
            self._addConnectionOut(sinkParam)

    def _addConnectionOut(self, sinkParam):
        self._connectionsOut[sinkParam] = Connection(self.nodegraph,
                                                     self.ramenParameter,
                                                     sinkParam)

    def _removeConnectionOut(self, sinkParam):
        connUI = self.getConnectionOutUI(sinkParam)
        if connUI is not None:
            connUI.delete()

    def getConnectionOutUI(self, sinkParam):
        return self._connectionsOut.get(sinkParam, None)

    def getConnectionInUI(self, sourceParam):
        # We actually need to go to the other UI item for this
        nodeUI = self.nodegraph.getNodeUI(sourceParam.node)
        paramUI = nodeUI.getParameterUI(sourceParam)
        connUI = paramUI.getConnectionOutUI(sourceParam)
        return connUI
