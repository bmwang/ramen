from ramen.signal import Signal
from ramen.node import parentChild
from ramen.node import connectable


class Parameter(parentChild.ParentChild, connectable.Connectable):
    def __init__(self, label=None, parameter_id=0, parent=None, index=0,
                 node=None):
        super(Parameter, self).__init__()
        # Simple properties with signals
        self._parameter_id = parameter_id
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
        self._connections_out = set()
        self._connections_in = set()

        # property signals
        self.parameter_id_changed = Signal()
        self.label_changed = Signal()
        self.index_changed = Signal()

        self.connection_added = Signal()
        self.connection_removed = Signal()
        self.sink_changed = Signal()
        self.source_changed = Signal()

        # TODO: this needs to fill in the other sink/source value
        # self.connectionModeChanged = Signal()
        # self.sink_changed.connect(self.connectionModeChanged.emit)
        # self.source_changed.connect(self.connectionModeChanged.emit)
        self.register_callbacks()
        if self._node is not None:
            self._node.parameter_added.emit(parameter=self, param=self)

    def delete(self):
        self.parent = None
        self.node = None

    def register_callbacks(self):
        if self._node is None:
            return
        self.connection_added.connect(self.node.connection_added.emit,
                                      parameter=self, param=self)
        self.connection_removed.connect(self.node.connection_removed.emit,
                                        parameter=self, param=self)
        self.sink_changed.connect(self.node.parameter_sink_changed.emit,
                                  parameter=self, param=self)
        self.source_changed.connect(self.node.parameter_source_changed.emit,
                                    parameter=self, param=self)

    def deregister_callbacks(self):
        if self._node is None:
            return
        self.connection_added.disconnect(self.node.connection_added.emit)
        self.connection_removed.disconnect(self.node.connection_removed.emit)
        self.sink_changed.disconnect(self.node.parameter_sink_changed.emit)
        self.source_changed.disconnect(self.node.parameter_source_changed.emit)

    def __repr__(self):
        '''fake convenience repr'''
        node_str = 'No node'
        if self.node is not None:
            node_str = 'Node: %s' % repr(self.node)

        return '<%s: %s/%s (%s)>' % (
                self.__class__.__name__, repr(self.parameter_id),
                self.label, node_str)

    @property
    def parameter_id(self):
        return self._parameter_id

    @parameter_id.setter
    def parameter_id(self, new_val):
        self._parameter_id = new_val
        self.parameter_id_changed.emit(parameter_id=self._parameter_id)

    @parameter_id.deleter
    def parameter_id(self):
        del self._parameter_id

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, new_val):
        self._label = new_val
        self.label_changed.emit(label=self._label)

    @label.deleter
    def label(self):
        del self._label

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, new_val):
        self._index = new_val
        self.index_changed.emit(index=self._index)

    @index.deleter
    def index(self):
        del self._index

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, new_node):
        if self._parent is not None:
            self.parent = None
        if self._node is not None:
            self.deregister_callbacks()
            self.parameter_removed.emit(parameter=self, param=self)
        self._node = new_node
        self.register_callbacks()
        self.parameter_added.emit(parameter=self, param=self)

    def is_transitively_connected(self, param):
        # TODO: two-sided BFS a la path tracing
        return param in self.connections

    @property
    def connection_subgraph(self):
        return self.node.parent

    def loft(self):
        # In ambiguous cases, loft the sink
        if self.sink:
            return self.loft_sink()
        if self.source:
            return self.loft_source()

    def loft_sink(self):
        if not self.sink:
            return None
        if self.node.parent is None:
            return None
        for tunnel_param in self.node.parent.tunnel_parameters:
            if self in tunnel_param.connections:
                return self.node.parent.get_parameter_for_tunnel(tunnel_param)
        lofted_param = Parameter(node=self.node.parent)
        lofted_param.sink = True
        self.node.parent.get_tunnel_parameter(lofted_param).connect(self)
        return lofted_param

    def loft_source(self):
        if not self.source:
            return None
        if self.node.parent is None:
            return None
        for tunnel_param in self.node.parent.tunnel_parameters:
            if self in tunnel_param.connections:
                return self.node.parent.get_parameter_for_tunnel(tunnel_param)
        lofted_param = Parameter(node=self.node.parent)
        lofted_param.source = True
        self.node.parent.get_tunnel_parameter(lofted_param).connect(self)
        return lofted_param

    def connect(self, param):
        # Easy case, connection in the same subgraph
        if self.connection_subgraph == param.connection_subgraph:
            return super(Parameter, self).connect(param)

        # Hard case, different parents
        # Loft up the one with more ancestors.
        # (in the case of equal length but different ancestors just choose
        # one and the other will be lofted in recursion)
        # Determine directionality
        # In ambiguous cases, prefer that we are the source
        self_is_source = True
        if self.source and param.sink:
            self_is_source = True
        elif self.sink and param.source:
            self_is_source = False
        else:
            print('unable to connect')

        deep_param = self
        surface_param = param
        deep_is_source = self_is_source
        if len(self.node.ancestors) < len(param.node.ancestors):
            deep_param = param
            surface_param = self
            deep_is_source = not self_is_source
        if deep_is_source:
            lofted_param = deep_param.loft_source()
        else:
            lofted_param = deep_param.loft_sink()
        if lofted_param is not None:
            return lofted_param.connect(surface_param)


class TunnelParameter(Parameter):
    '''A Parameter for connecting a node's siblings to its children. Attaches
    to an existing parameter, or creates one on a specified node. Only valid
    if the node containing the parameter accepts children.
    '''
    def __init__(self, parameter):
        self._tunneled_parameter = parameter
        super(TunnelParameter, self).__init__(node=parameter.node)

        self.tunneled_parameterChanged = Signal()
        self.sink_changed = Signal()
        self.source_changed = Signal()

    def register_node_callbacks(self):
        if self.node is None:
            return
        self.tunneled_parameter.connect(self.node.tunneled_parameter_changed,
                                        parameter=self, param=self)

    def deregister_node_callbacks(self):
        if self.node is None:
            return
        self.tunneled_parameter.connect(self.node.tunneled_parameter_changed,
                                        parameter=self, param=self)

    def register_tunneled_parameter_callbacks(self):
        self.tunneled_parameter.sink_changed.connect(self.sink_changed.emit)
        self.tunneled_parameter.source_changed.connect(
            self.source_changed.emit)

    def deregister_tunneled_parameter_callbacks(self):
        self.tunneled_parameter.sink_changed.disconnect(self.sink_changed.emit)
        self.tunneled_parameter.source_changed.disconnect(
                self.source_changed.emit)

    @property
    def connection_subgraph(self):
        return self.node

    @property
    def tunneled_parameter(self):
        return self._tunneled_parameter

    @tunneled_parameter.setter
    def tunneled_parameter(self, param):
        self.deregister_tunneled_parameter_callbacks()
        self._parameter = param

    @property
    def sink(self):
        return self.tunneled_parameter.source

    @sink.setter
    def sink(self, sink):
        self.tunneled_parameter.source = sink

    @property
    def source(self):
        return self.tunneled_parameter.sink

    @source.setter
    def source(self, source):
        self.tunneled_parameter.sink = source

    def loft_source(self):
        if self.sink:
            return self._parameter
        for tunnel_param in self.node.tunnel_parameters:
            if self in tunnel_param.connections_in:
                return tunnel_param
        new_param = Parameter(node=self.node)
        new_param.source = True
        self.node.get_tunnel_parameter(new_param).connect(self)
        return new_param

    def loft_sink(self):
        if self.source:
            return self._parameter
        for tunnel_param in self.node.tunnel_parameters:
            if self in tunnel_param.connections_out:
                return tunnel_param
        new_param = Parameter(node=self.node)
        new_param.sink = True
        self.node.get_tunnel_parameter(new_param).connect(self)
        return new_param
