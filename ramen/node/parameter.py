from ..signal import Signal
from . import parentChild
from . import connectable

class Parameter(parentChild.ParentChild, connectable.Connectable):
    def __init__(self, label=None, parameterId=0, parent=None, index=0,
            node=None):
        super(Parameter, self).__init__()
        # Simple properties with signals
        self._parameterId = parameterId
        self._label = label
        self._inbex = index

        # More complicated properties
        # Whether or not this parameter can take connections
        # Source -> Sink
        # If this parameter itself does not take connections, connections
        # to this parameter will flow to the first child of the parameter that
        # does
        self._sink = False
        self._source = False
        # Attached node
        self._node = node
        # Outward and inward connections
        self._connectionsOut = set()
        self._connectionsIn = set()

        # property signals
        self.parameterIdChanged = Signal()
        self.labelChanged = Signal()
        self.indexChanged = Signal()

        self.connectionAdded = Signal()
        self.connectionRemoved = Signal()
        self.sinkChanged = Signal()
        self.sourceChanged = Signal()

        # TODO: this needs to fill in the other sink/source value
        # self.connectionModeChanged = Signal()
        # self.sinkChanged.connect(self.connectionModeChanged.emit)
        # self.sourceChanged.connect(self.connectionModeChanged.emit)
        self.registerCallbacks()
        if self._node is not None:
            self._node.parameterAdded.emit(parameter=self, param=self)

    def delete(self):
        self.parent = None
        self.node = None

    def registerCallbacks(self):
        if self._node is None:
            return
        self.connectionAdded.connect(self.node.connectionAdded.emit,
                parameter=self, param=self)
        self.connectionRemoved.connect(self.node.connectionRemoved.emit,
                parameter=self, param=self)
        self.sinkChanged.connect(self.node.parameterSinkChanged.emit,
                parameter=self, param=self)
        self.sourceChanged.connect(self.node.parameterSourceChanged.emit,
                parameter=self, param=self)

    def deregisterCallbacks(self):
        if self._node is None:
            return
        self.connectionAdded.disconnect(self.node.connectionAdded.emit)
        self.connectionRemoved.disconnect(self.node.connectionRemoved.emit)
        self.sinkChanged.disconnect(self.node.parameterSinkChanged.emit)
        self.sourceChanged.disconnect(self.node.parameterSourceChanged.emit)

    def __repr__(self):
        '''fake convenience repr'''
        nodeStr = 'No node'
        if self.node is not None:
            nodeStr = 'Node: %s' % repr(self.node)

        return '<%s: %s/%s (%s)>' % (
                self.__class__.__name__, repr(self.parameterId),
                self.label, nodeStr)

    @property
    def parameterId(self):
        return self._parameterId

    @parameterId.setter
    def parameterId(self, newVal):
        self._parameterId = newVal
        self.parameterIdChanged.emit(parameterId=self._parameterId)

    @parameterId.deleter
    def parameterId(self):
        del self._parameterId

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, newVal):
        self._label = newVal
        self.labelChanged.emit(label=self._label)

    @label.deleter
    def label(self):
        del self._label


    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, newVal):
        self._index = newVal
        self.indexChanged.emit(index=self._index)

    @index.deleter
    def index(self):
        del self._index


    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, newNode):
        if self._parent is not None:
            self.parent = None
        if self._node is not None:
            self.deregisterCallbacks()
            self.parameterRemoved.emit(parameter=self, param=self)
        self._node = newNode
        self.registerCallbacks()
        self.parameterAdded.emit(parameter=self, param=self)

    def isTransitivelyConnected(self, param):
        # TODO: two-sided BFS a la path tracing
        return param in self.connections

    @property
    def connectionSubgraph(self):
        return self.node.parent

    def loft(self):
        # In ambiguous cases, loft the sink
        if self.sink:
            return self.loftSink()
        if self.source:
            return self.loftSource()

    def loftSink(self):
        if not self.sink:
            return None
        if self.node.parent is None:
            return None
        for tunnelParam in self.node.parent.tunnelParameters:
            if self in tunnelParam.connections:
                return self.node.parent.getParameterForTunnel(tunnelParam)
        loftedParam = Parameter(node=self.node.parent)
        loftedParam.sink = True
        self.node.parent.getTunnelParameter(loftedParam).connect(self)
        return loftedParam

    def loftSource(self):
        if not self.source:
            return None
        if self.node.parent is None:
            return None
        for tunnelParam in self.node.parent.tunnelParameters:
            if self in tunnelParam.connections:
                return self.node.parent.getParameterForTunnel(tunnelParam)
        loftedParam = Parameter(node=self.node.parent)
        loftedParam.source = True
        self.node.parent.getTunnelParameter(loftedParam).connect(self)
        return loftedParam

    def connect(self, param):
        # Easy case, connection in the same subgraph
        if self.connectionSubgraph == param.connectionSubgraph:
            return super(Parameter, self).connect(param)

        # Hard case, different parents
        # Loft up the one with more ancestors.
        # (in the case of equal length but different ancestors just choose
        # one and the other will be lofted in recursion)
        # Determine directionality
        # In ambiguous cases, prefer that we are the source
        selfIsSource = True
        if self.source and param.sink:
            selfIsSource = True
        elif self.sink and param.source:
            selfIsSource = False
        else:
            print('unable to connect')

        deepParam = self
        surfaceParam = param
        deepIsSource = selfIsSource
        if len(self.node.ancestors) < len(param.node.ancestors):
            deepParam = param
            surfaceParam = self
            deepIsSource = not selfIsSource
        if deepIsSource:
            loftedParam = deepParam.loftSource()
        else:
            loftedParam = deepParam.loftSink()
        if loftedParam is not None:
            return loftedParam.connect(surfaceParam)

class TunnelParameter(Parameter):
    '''A Parameter for connecting a node's siblings to its children. Attaches
    to an existing parameter, or creates one on a specified node. Only valid
    if the node containing the parameter accepts children.
    '''
    def __init__(self, parameter):
        self._tunneledParameter = parameter
        super(TunnelParameter, self).__init__(node=parameter.node)

        self.tunneledParameterChanged = Signal()
        self.sinkChanged = Signal()
        self.sourceChanged = Signal()

    def registerNodeCallbacks(self):
        if self.node is None:
            return
        self.tunneledParameter.connect(self.node.tunneledParameterChanged,
                parameter=self, param=self)

    def deregisterNodeCallbacks(self):
        if self.node is None:
            return
        self.tunneledParameter.connect(self.node.tunneledParameterChanged,
                parameter=self, param=self)

    def registerTunneledParameterCallbacks(self):
        self.tunneledParameter.sinkChanged.connect(self.sinkChanged.emit)
        self.tunneledParameter.sourceChanged.connect(self.sourceChanged.emit)

    def deregisterTunneledParameterCallbacks(self):
        self.tunneledParameter.sinkChanged.disconnect(self.sinkChanged.emit)
        self.tunneledParameter.sourceChanged.disconnect(
                self.sourceChanged.emit)

    @property
    def connectionSubgraph(self):
        return self.node

    @property
    def tunneledParameter(self):
        return self._tunneledParameter

    @tunneledParameter.setter
    def tunneledParameter(self, param):
        self.deregisterTunneledParameterCallbacks()
        self._parameter = param

    @property
    def sink(self):
        return self.tunneledParameter.source

    @sink.setter
    def sink(self, sink):
        self.tunneledParameter.source = sink

    @property
    def source(self):
        return self.tunneledParameter.sink

    @source.setter
    def source(self, source):
        self.tunneledParameter.sink = source

    def loftSource(self):
        if self.sink:
            return self._parameter
        for tunnelParam in self.node.tunnelParameters:
            if self in tunnelParam.connectionsIn:
                return tunnelParam
        newParam = Parameter(node=self.node)
        newParam.source = True
        self.node.getTunnelParameter(newParam).connect(self)
        return newParam

    def loftSink(self):
        if self.source:
            return self._parameter
        for tunnelParam in self.node.tunnelParameters:
            if self in tunnelParam.connectionsOut:
                return tunnelParam
        newParam = Parameter(node=self.node)
        newParam.sink = True
        self.node.getTunnelParameter(newParam).connect(self)
        return newParam


