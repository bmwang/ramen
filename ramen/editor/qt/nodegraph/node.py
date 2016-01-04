from PyQt4 import QtGui, QtCore
from ramen.editor.qt.nodegraph.nodegraphscene import NodegraphScene
from ramen.editor.qt.nodegraph.parameter import Parameter


class Node(QtGui.QGraphicsItem):
    def __init__(self, nodegraph, ramenNode, *args, **kwargs):
        if ramenNode.parent is not None:
            kwargs['scene'] = nodegraph.getNodeUI(ramenNode.parent).scene
        super(Node, self).__init__(*args, **kwargs)
        self._nodegraph = nodegraph
        self._ramenNode = ramenNode
        self._parameterUIs = {}

        self._backdrop = QtGui.QGraphicsRectItem(self)
        self._label = QtGui.QGraphicsTextItem(self)

        self.registerRamenCallbacks()
        self.syncParameters()
        self.updateGeo()

    @property
    def nodegraph(self):
        return self._nodegraph

    @property
    def ramenNode(self):
        return self._ramenNode

    def registerRamenCallbacks(self):
        self._ramenNode.pos_changed.connect(self.updateGeo)
        self._ramenNode.selected_changed.connect(self.updateGeo)
        self._ramenNode.label_changed.connect(self.updateGeo)
        self._ramenNode.parameter_added.connect(self._addParameter)
        self._ramenNode.parameter_removed.connect(self._removeParameter)

    def deregisterRamenCallbacks(self):
        self._ramenNode.pos_changed.disconnect(self.updateGeo)
        self._ramenNode.selected_changed.disconnect(self.updateGeo)
        self._ramenNode.label_changed.disconnect(self.updateGeo)
        self._ramenNode.parameter_added.disconnect(self._addParameter)
        self._ramenNode.parameter_removed.disconnect(self._removeParameter)

    def _addParameter(self, parameter):
        for ancestor in parameter.ancestors:
            if ancestor not in self._parameterUIs:
                self._addParameter(ancestor)
        parentUI = self
        if parameter.parent is not None:
            parentUI = self._parameterUIs[parameter.parent]
        self._parameterUIs[parameter] = Parameter(self.nodegraph,
                                                  parameter,
                                                  parentUI)
        if parameter.parent is not None:
            self._parameterUIs[parameter.parent].updateGeo()

    def _removeParameter(self, parameter):
        self.scene().removeItem(self._parameterUIs[parameter])
        del self._parameterUIs[parameter]
        if parameter.parent is not None:
            self._parameterUIs[parameter.parent].updateGeo()

    def getParameterUI(self, parameter):
        return self._parameterUIs[parameter]

    def syncParameters(self):
        ramenParameters = set(self.ramenNode.parameters)
        knownParameters = set(self._parameterUIs.keys())
        parametersToRemove = knownParameters.difference(ramenParameters)
        parametersToAdd = ramenParameters.difference(knownParameters)
        for parameter in parametersToRemove:
            self._removeParameter(parameter)
        for parameter in parametersToAdd:
            self._addParameter(parameter)

    def updateGeo(self):
        # Temp colors for now -- style later
        self._label.setDefaultTextColor(QtGui.QColor(255, 255, 255, 200))
        if self.ramenNode.selected:
            self._backdrop.setPen(QtGui.QColor(200, 200, 200, 200))
        else:
            self._backdrop.setPen(QtGui.QColor(100, 100, 100, 200))
        self._backdrop.setBrush(QtGui.QColor(30, 30, 30, 200))

        backdropRect = QtCore.QRectF(0, 0, 100, 30)
        self.setPos(*self.ramenNode.pos)
        if self.ramenNode.label is not None:
            self._label.setPlainText(self.ramenNode.label)
            backdropRect |= self._label.boundingRect()

        if len(self.ramenNode.parameters) > 0:
            rootParamUI = self._parameterUIs[self.ramenNode.root_parameter]
            rootParamUIPos = self._label.boundingRect().height()
            rootParamUI.setPos(0, rootParamUIPos)
            backdropRect |= rootParamUI.boundingRect().translated(
                0, rootParamUIPos)

        self._backdrop.setRect(backdropRect)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, *args):
        # TODO: figure out what this does
        pass

    @property
    def node(self):
        return self._ramenNode


class SubgraphNode(Node):
    def __init__(self, *args, **kwargs):
        super(SubgraphNode, self).__init__(*args, **kwargs)
        self._scene = NodegraphScene(self)

    @property
    def scene(self):
        return self._scene
