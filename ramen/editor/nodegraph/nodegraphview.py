from PyQt4 import QtCore, QtGui
from ramen.signal import Signal


class NodegraphView(QtGui.QGraphicsView):
    def __init__(self, nodegraph, parent=None):
        super(NodegraphView, self).__init__(parent)
        self.nodegraph = nodegraph

    def viewSubgraph(self, subgraphNode):
        nodeUI = self.nodegraph.getNodeUI(subgraphNode)
        if nodeUI is None:
            raise RuntimeError('No Node UI for %s' % subgraphNode)
        self.setScene(nodeUI.scene)