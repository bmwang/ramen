from .signal import Signal
from . import node

class Graph(object):
    '''The graph. Contains all our nodes.'''
    def __init__(self):
        # ID -> node
        self._nodes = {}
        self._rootNodeId = None

        self._selectedNodes = set()

        # Nodes
        self.nodeAdded = Signal()
        self.nodeRemoved = Signal()
        self.nodeParentChanged = Signal()

        # Parameters
        self.parameterAdded = Signal()
        self.parameterRemoved = Signal()
        self.parameterSinkChanged = Signal()
        self.parameterSourceChanged = Signal()

        # Connections
        self.connectionAdded = Signal()
        self.connectRemoved = Signal()

        # node attributes
        self.nodeIdChanged = Signal()
        self.nodeLabelChanged = Signal()
        self.nodeAttributesChanged = Signal()
        self.nodePosChanged = Signal()
        self.nodeSelectedChanged = Signal()
        self.nodeNameChanged = Signal()

        # connections
        self.connectionAdded = Signal()
        self.connectionRemoved = Signal()

        self.nodeAdded.connect(self._nodeAddedCallback)
        self.nodeRemoved.connect(self._nodeRemovedCallback)


    @property
    def nodes(self):
        return self._nodes.values()

    @nodes.setter
    def nodes(self, newNodes):
        curNodes = set(self._nodes.values())
        newNodes = set(newNodes)
        # Don't delete the root node!
        newNodes.add(self.rootNode)
        nodesToAdd = newNodes.difference(curNodes)
        nodesToRemove = curNodes.difference(newNodes)
        for node in nodesToAdd:
            node.graph = self
        for node in nodesToRemove:
            node.graph = None

    @nodes.deleter
    def nodes(self):
        self.clear()

    def createNode(self, *args, **kwargs):
        # convenience
        kwargs['graph'] = self
        return node.Node(*args, **kwargs)

    def clear(self):
        self.nodes = []

    @property
    def selectedNodes(self):
        return set(self._selectedNodes)

    def __getitem__(self, nodeId):
        return self._nodes.get(nodeId, None)

    def __contains__(self, nodeId):
        return nodeId in self._nodes

    @property
    def selecetdNodes(self):
        return set(self._selectedNodes)

    @selectedNodes.setter
    def selectedNodes(self, selectedNodes):
        nodesToSelect = selectedNodes.difference(self._selectedNodes)
        nodesToUnselect = self._selectedNodes.difference(selectedNodes)
        for node in nodesToSelect:
            node.setSelected(True)
        for node in nodesToUnselect:
            node.setSelected(False)

    def clearSelecetion(self):
        for node in self.getSelectedNodes():
            node.setSelected(False)

    def _uniquefyNodeId(self, nodeId):
        if nodeId not in self:
            return nodeId
        # The NodeID can be either a string or int (or anything else you want,
        # but we need to be able to make a unique type)
        if type(nodeId) == str:
            attempt = 0
            uniqueNodeId = nodeId
            while uniqueNodeId in self:
                attempt += 1
                uniqueNodeId = nodeId + '_' + str(attempt)
            return uniqueNodeId

        elif type(nodeId) == int or type(nodeId) == float:
            while nodeId in self:
                nodeId += 1
            return nodeId

        print('Warning! Unable to unquefy nodeId type %s' % str(type(nodeId)))
        return nodeId

    @property
    def rootNode(self):
        if self._rootNodeId is None:
            self._rootNodeId = self._uniquefyNodeId('root')
            self._rootNode = node.SubgraphNode(nodeId=self._rootNodeId,
                    graph=self)
            return self._rootNode
        return self[self._rootNodeId]

    def _nodeAddedCallback(self, node):
        nodeId = node.nodeId
        if nodeId in self:
            nodeId = self._uniquefyNodeId(nodeId)
            node.nodeId = nodeId
        if node.parent == None and nodeId != self._rootNodeId:
            node.parent = self.rootNode
        self._nodes[nodeId] = node

    def _nodeRemovedCallback(self, node):
        if node.nodeId not in self:
            return
        if node.nodeId == self._rootNodeId:
            print('Warning: deleting root node')
            self._rootNodeId = None
        del self._nodes[node.nodeId]


