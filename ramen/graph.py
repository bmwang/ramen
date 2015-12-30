from ramen.signal import Signal
from ramen import node


class Graph(object):
    '''The graph. Contains all our nodes.'''
    def __init__(self):
        # ID -> node
        self._nodes = {}
        self._root_node_id = None

        self._selected_nodes = set()

        # Nodes
        self.node_added = Signal()
        self.node_removed = Signal()
        self.node_parent_changed = Signal()

        # Parameters
        self.parameter_added = Signal()
        self.parameter_removed = Signal()
        self.parameter_sink_changed = Signal()
        self.parameter_source_changed = Signal()

        # Connections
        self.connection_added = Signal()
        self.connection_removed = Signal()

        # node attributes
        self.node_id_changed = Signal()
        self.node_label_changed = Signal()
        self.node_attributes_changed = Signal()
        self.node_pos_changed = Signal()
        self.node_selected_changed = Signal()
        self.node_name_changed = Signal()

        self.node_added.connect(self._node_added_callback)
        self.node_removed.connect(self._node_removed_callback)
        self.node_selected_changed.connect(
            self._node_selected_changed_callback)

    @property
    def nodes(self):
        return self._nodes.values()

    @nodes.setter
    def nodes(self, new_nodes):
        cur_nodes = set(self._nodes.values())
        new_nodes = set(new_nodes)
        # Don't delete the root node!
        new_nodes.add(self.root_node)
        nodes_to_add = new_nodes.difference(cur_nodes)
        nodes_to_remove = cur_nodes.difference(new_nodes)
        for node in nodes_to_add:
            node.graph = self
        for node in nodes_to_remove:
            node.graph = None

    @nodes.deleter
    def nodes(self):
        self.clear()

    def create_node(self, *args, **kwargs):
        # convenience
        kwargs['graph'] = self
        return node.Node(*args, **kwargs)

    def clear(self):
        self.nodes = []

    @property
    def selected_nodes(self):
        return set(self._selected_nodes)

    def __getitem__(self, node_id):
        return self._nodes.get(node_id, None)

    def __contains__(self, node_id):
        return node_id in self._nodes

    @property
    def selected_nodes(self):
        return set(self._selected_nodes)

    @selected_nodes.setter
    def selected_nodes(self, selected_nodes):
        selected_nodes = set(selected_nodes)
        nodes_to_select = selected_nodes.difference(self._selected_nodes)
        nodes_to_unselect = self._selected_nodes.difference(selected_nodes)
        for node in nodes_to_select:
            node.selected = True
        for node in nodes_to_unselect:
            node.selected = False

    def clear_selection(self):
        for node in self.get_selected_nodes():
            node.set_selected(False)

    def _uniquefy_node_id(self, node_id):
        if node_id not in self:
            return node_id
        # The node_id can be either a string or int (or anything else you want,
        # but we need to be able to make a unique type)
        if type(node_id) == str:
            attempt = 0
            unique_node_id = node_id
            while unique_node_id in self:
                attempt += 1
                unique_node_id = node_id + '_' + str(attempt)
            return unique_node_id

        elif type(node_id) == int or type(node_id) == float:
            while node_id in self:
                node_id += 1
            return node_id

        print('Warning! Unable to unquefy node_id type %s' %
              str(type(node_id)))
        return node_id

    @property
    def root_node(self):
        if self._root_node_id is None:
            self._root_node_id = self._uniquefy_node_id('root')
            self._root_node = node.SubgraphNode(node_id=self._root_node_id,
                                                graph=self)
            return self._root_node
        return self[self._root_node_id]

    def _node_added_callback(self, node):
        node_id = node.node_id
        if node_id in self:
            node_id = self._uniquefy_node_id(node_id)
            node.node_id = node_id
        if node.parent is None and node_id != self._root_node_id:
            node.parent = self.root_node
        self._nodes[node_id] = node

    def _node_removed_callback(self, node):
        if node.node_id not in self:
            return
        if node.node_id == self._root_node_id:
            print('Warning: deleting root node')
            self._root_node_id = None
        del self._nodes[node.node_id]

    def _node_selected_changed_callback(self, node):
        if not node.selected and node in self.selected_nodes:
            self._selected_nodes.remove(node)
        elif node.selected and node not in self.selected_nodes:
            self._selected_nodes.add(node)
