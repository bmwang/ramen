from PyQt4 import QtGui, QtCore
from ramen.editor.nodegraph.nodegraphscene import NodegraphScene


class Node(QtGui.QGraphicsItem):
    def __init__(self, nodegraph, ramenNode, *args, **kwargs):
        if ramenNode.parent is not None:
            kwargs['scene'] = nodegraph.getNodeUI(ramenNode.parent).scene
        super(Node, self).__init__(*args, **kwargs)
        self._nodegraph = nodegraph
        self._ramenNode = ramenNode
        self._backdrop = QtGui.QGraphicsRectItem(self)
        self._label = QtGui.QGraphicsTextItem(self)

        self.registerRamenCallbacks()
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

    def deregisterRamenCallbacks(self):
        self._ramenNode.pos_changed.disconnect(self.updateGeo)
        self._ramenNode.selected_changed.disconnect(self.updateGeo)
        self._ramenNode.label_changed.disconnect(self.updateGeo)

    def updateGeo(self):
        # Temp colors for now -- style later
        self._label.setDefaultTextColor(QtGui.QColor(255, 255, 255, 200))
        if self.ramenNode.selected:
            self._backdrop.setPen(QtGui.QColor(200, 200, 200, 200))
        else:
            self._backdrop.setPen(QtGui.QColor(100, 100, 100, 200))
        self._backdrop.setBrush(QtGui.QColor(30, 30, 30, 200))

        self.setPos(*self.ramenNode.pos)
        self._backdrop.setRect(QtCore.QRectF(0, 0, 100, 30))
        if self.ramenNode.label is not None:
            self._label.setPlainText(self.ramenNode.label)

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
