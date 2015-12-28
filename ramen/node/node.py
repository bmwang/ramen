from ramen.signal import Signal
from ramen.node import parentChild
from ramen.node import parameter


class Node(parentChild.ParentChild):
    def __init__(self, parent=None, label=None, node_id=0, graph=None):
        super(Node, self).__init__()
        # If a parent is provided, use the parent's graph.
        if parent is not None:
            if parent.graph is not graph and graph is not None:
                print("Warning: Specified graph differs from parent's graph. "
                      "Using parent's graph")
            graph = parent.graph

        if graph is None:
            raise RuntimeError('Node created with an invalid graph')

        # Properties
        self._node_id = node_id
        self._label = label
        self._pos = (0, 0)
        self._selected = False
        self._graph = graph
        self._parameters = {}
        self._root_parameter = None

        # Signals
        self.node_id_changed = Signal()
        self.label_changed = Signal()
        self.pos_changed = Signal()
        self.selected_changed = Signal()

        self.attributes_changed = Signal()
        # "attributes_changed" is really one of four other signals
        # TODO: we could change the args into a dict
        self.pos_changed.connect(self.attributes_changed.emit)
        self.selected_changed.connect(self.attributes_changed.emit)
        self.label_changed.connect(self.attributes_changed.emit)

        # Parameters
        self.parameter_added = Signal()
        self.parameter_removed = Signal()

        # Parameter's signals loft up
        self.connection_added = Signal()
        self.connection_removed = Signal()
        self.parameter_sink_changed = Signal()
        self.parameter_source_changed = Signal()

        # Connect parameter_added to callbacks here
        self.parameter_added.connect(self._parameter_added_callback)
        self.parameter_removed.connect(self._parameter_removed_callback)

        self.parent = parent
        self.accepts_children = False
        self.register_callbacks()
        self._graph.node_added.emit(node=self)

    def delete(self):
        self.parent = None
        self.graph = None

    def __repr__(self):
        # Fake repr for readability
        label_str = ''
        if self.label is not None:
            label_str = '/%s' % self.label
        return '<%s: %s%s>' % (self.__class__.__name__, self.node_id,
                               label_str)

    def register_callbacks(self):
        # Graph level signals
        self.pos_changed.connect(self.graph.node_pos_changed.emit, node=self)
        self.selected_changed.connect(self.graph.node_selected_changed.emit,
                                      node=self)
        self.node_id_changed.connect(self.graph.node_id_changed.emit,
                                     node=self)
        self.label_changed.connect(self.graph.node_label_changed.emit,
                                   node=self)
        self.parent_changed.connect(self.graph.node_parent_changed.emit,
                                    node=self)
        self.attributes_changed.connect(
            self.graph.node_attributes_changed.emit, node=self)

        # lofted parameter signals
        self.connection_added.connect(self.graph.connection_added.emit)
        self.connection_removed.connect(self.graph.connection_removed.emit)
        self.parameter_sink_changed.connect(
            self.graph.parameter_sink_changed.emit)
        self.parameter_source_changed.connect(
            self.graph.parameter_source_changed.emit)

    def deregister_callbacks(self):
        # Graph level signals
        self.pos_changed.disconnect(self.graph.node_pos_changed.emit)
        self.selected_changed.disconnect(self.graph.node_selected_changed.emit)
        self.node_id_changed.disconnect(self.graph.node_id_changed.emit)
        self.label_changed.disconnect(self.graph.node_label_changed.emit)
        self.parent_changed.disconnect(self.graph.node_parent_changed.emit)
        self.attributes_changed.disconnect(
                self.graph.node_attributes_changed.emit)

        # lofted parameter signals
        self.connection_added.disconnect(self.graph.connection_added.emit)
        self.connection_removed.disconnect(self.graph.connection_removed.emit)
        self.parameter_sink_changed.disconnect(
                self.graph.parameter_sink_changed.emit)
        self.parameter_source_changed.disconnect(
                self.graph.parameter_source_changed.emit)

    @property
    def node_id(self):
        return self._node_id

    @node_id.setter
    def node_id(self, val):
        old_node_id = self._node_id
        self._node_id = val
        self.node_id_changed.emit(old_node_id=old_node_id,
                                  node_id=self._node_id)

    @node_id.deleter
    def node_id(self):
        del self._node_id

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, val):
        self._label = val
        self.label_changed.emit(label=self._label)

    @label.deleter
    def label(self):
        del self._label

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, val):
        self._pos = val
        self.pos_changed.emit(pos=self._pos)

    @pos.deleter
    def pos(self):
        del self._pos

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, val):
        self._selected = val
        self.selected_changed.emit(selected=self._selected)

    @selected.deleter
    def selected(self):
        del self._selected

    @property
    def root_parameter(self):
        if self._root_parameter is None:
            self._root_parameter = parameter.Parameter(node=self)
        return self._root_parameter

    @root_parameter.setter
    def root_parameter(self, root_parameter):
        # TODO
        return

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, new_graph):
        if self._graph == new_graph:
            return
        self.deregister_callbacks()
        if self.parent is not None and self.parent.graph != new_graph:
            self.parent = None
        self._graph.node_removed.emit(node=self)
        self._graph = new_graph
        if self._graph is not None:
            self.register_callbacks()
            self._graph.node_added.emit(node=self)

    @property
    def parameters(self):
        return list(self._parameters.values())

    def get_parameter(self, param_id):
        return self._parameters.get(param_id, None)

    def __getitem__(self, param_id):
        return self.get_parameter(param_id)

    @parameters.setter
    def parameters(self, newParams):
        # TODO
        return

    @property
    def accepts_children(self):
        return False

    @parentChild.ParentChild.accepts_children.setter
    def accepts_children(self, accepts_children):
        # I don't care what you give me, I don't accept children.
        parentChild.ParentChild.accepts_children.fset(self, False)

    def create_parameter(self, *args, **kwargs):
        kwargs['node'] = self
        return parameter.Parameter(*args, **kwargs)

    def delete_parameter(self, parameter):
        parameter.delete()

    def _parameter_added_callback(self, parameter):
        if parameter.parameter_id in self._parameters:
            parameter.parameter_id = self._uniquefy_parameter_id(
                    parameter.parameter_id)
        self._parameters[parameter.parameter_id] = parameter

    def _parameter_removed_callback(self, parameter):
        if param.parameter_id in self._parameters:
            del self._parameters[param.parameter_id]

    def _uniquefy_parameter_id(self, param_id):
        if not param_id not in self._parameters:
            return param_id
        # The param_id can be either a string or int (or anything you want,
        # but we need to be able to make a unique type)
        if type(param_id) == type(str):
            attempt = 0
            unique_id = param_id
            while unique_id in self._parameters:
                attempt += 1
                unique_id = param_id + '_' + str(attempt)
            return unique_id

        elif type(param_id) == type(int) or type(param_id) == type(float):
            while unique_id in self._parameters:
                unique_id += 1
            return unique_id

        print('Warning! Unable to unquefy node_id type %s' %
              str(type(node_id)))
        return param_id


class SubgraphNode(Node):
    def __init__(self, *args, **kwargs):
        super(SubgraphNode, self).__init__(*args, **kwargs)
        self.accepts_children = True
        self._tunnel_parameters = {}
        self._parameter_to_tunnel = {}
        self._tunnel_to_parameter = {}

    @property
    def accepts_children(self):
        return True

    @parentChild.ParentChild.accepts_children.setter
    def accepts_children(self, accepts_children):
        # I don't care what you give me, I always accept children.
        parentChild.ParentChild.accepts_children.fset(self, True)

    def _parameter_added_callback(self, param):
        # This is pretty dirty, TODO: clean up
        if (param.parameter_id in self._parameters or
                param.parameter_id in self._tunnel_parameters):
            param.parameter_id = self._uniquefy_parameter_id(
                param.parameter_id)

        if isinstance(param, parameter.TunnelParameter):
            self._tunnel_parameters[param.parameter_id] = param
        else:
            super(SubgraphNode, self)._parameter_added_callback(param)
            tunnel = parameter.TunnelParameter(parameter=param)
            self._parameter_to_tunnel[param] = tunnel
            self._tunnel_to_parameter[tunnel] = param

    def _parameter_removed_callback(self, param):
        # This is pretty dirty, TODO: clean up
        if isinstance(param, parameter.TunnelParameter):
            if param.parameter_id in self._tunnel_parameters:
                del self._tunnel_parameters[param.parameter_id]
                if param in self._tunnel_to_parameter:
                    self._tunnel_to_parameter[param].node = None
        else:
            tunnel_param = self.get_tunnel_parameter(param)
            tunnel_param.node = None
            tunnel_param.tunneledParameter = None
            super(SubgraphNode, self)._parameter_added_callback(param)
            del self._parameter_to_tunnel[param]
            del self._tunnel_to_parameter[tunnel_param]

    def get_tunnel_parameter(self, param):
        return self._parameter_to_tunnel.get(param, None)

    def get_parameter_for_tunnel(self, tunnel):
        return self._tunnel_to_parameter.get(tunnel, None)

    @property
    def tunnel_parameters(self):
        return list(self._tunnel_parameters.values())
