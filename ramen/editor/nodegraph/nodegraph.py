from PyQt4 import QtCore, QtGui
import ramen
from ramen.editor.nodegraph import nodegraphview

# I realize that PyQt uses mixedCase, and Ramen/Python standard lib uses
# underscores, so there is some weird mixing here.
# idk what to do in this awkward situation..
# I guess I'll just keep all the code dealing with Qt as mixedCase?


class Nodegraph(QtGui.QWidget):
    def __init__(self, graph=None, parent=None):
        super(Nodegraph, self).__init__(parent)
        if graph is None:
            # If no graph specified, create one
            graph = ramen.Graph()
        self._graph = graph
        self._nodegraphView = nodegraphview.NodegraphView(self)

        self._ramenToUI = {}
        self._UIToRamen = {}

        layout = QtGui.QStackedLayout()
        layout.setStackingMode(QtGui.QStackedLayout.StackAll)
        layout.addWidget(self._nodegraphView)
        self.setLayout(layout)

        self.syncFromRamen()
        self.registerRamenCallbacks()

        self._nodegraphView.viewSubgraph(self.graph.root_node)

    def registerRamenCallbacks(self):
        self.graph.node_added.connect(self._addNode)
        self.graph.node_removed.connect(self._removeNode)
        self.graph.node_parent_changed.connect(self._reparentNode)

    def deregisterRamenCallbacks(self):
        self.graph.node_added.disconnect(self._addNode)
        self.graph.node_removed.disconnect(self._removeNode)
        self.graph.node_parent_changed.disconnect(self._reparentNode)

    def syncFromRamen(self):
        # TODO: difference of nodes in the editor and not
        for node in self.graph.nodes:
            self._addNode(node)

    def getNodeUI(self, node):
        return self._ramenToUI.get(node, None)

    def _addNode(self, node):
        # This should be in a delegate?
        uiMapping = {
            ramen.node.Node: ramen.editor.nodegraph.Node,
            ramen.node.SubgraphNode: ramen.editor.nodegraph.SubgraphNode,
        }
        if node not in self._ramenToUI:
            # If this node's ancestors haven't been added, make sure they are.
            for ancestor in node.ancestors:
                self._addNode(ancestor)
            uiNode = uiMapping[type(node)](self, node)
            self._ramenToUI[node] = uiNode
            self._UIToRamen[uiNode] = node

    def _removeNode(self, node):
        if node in self._ramenToUI:
            uiNode = self._ramenToUI[node]
            uiScene = uiNode.scene()
            if uiScene is not None:
                uiScene.removeItem(uiNode)
            del self._ramenToUI[node]
            del self._UIToRamen[uiNode]

    def _reparentNode(self, node):
        # Disconnect callbacks because this node is only being deleted in
        # the editor, and not from the graph itself.
        # TODO: this could be handled more cleanly
        uiNode = self.getNodeUI(node)
        if uiNode is None:
            # This node is being parented in its creation
            return
        uiNode.deregisterRamenCallbacks()
        self._removeNode(node)
        self._addNode(node)

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, graph):
        self.deregisterRamenCallbacks()
        self._graph = graph
        self.syncFromRamen()
        self.registerRamenCallbacks()
