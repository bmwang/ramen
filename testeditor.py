from __future__ import print_function
import sys
from PyQt4 import QtGui, QtCore
import ramen

# Quick tests on how to use the editor
# Will flesh out actual tests later


app = QtGui.QApplication(sys.argv)
nodegraph = ramen.editor.qt.nodegraph.Nodegraph()
nodegraph.resize(500, 500)
nodegraph.show()
nodegraph.raise_()

graph = nodegraph.graph
node_a = graph.create_node(label='a')
node_b = graph.create_node(label='b')
node_c = graph.create_node(label='c')

param_a = node_a.create_parameter(label='param a')
param_a.source = True
param_a2 = node_a.create_parameter(label='param a2')
param_b = node_b.create_parameter(label='param b')
param_b.sink = True
param_c = node_c.create_parameter(label='param c')


param_a.connect(param_b)

assert(nodegraph.getNodeUI(node_a) is not None)
assert(nodegraph.getNodeUI(node_b) is not None)

node_a.pos = (0, 0)
node_b.pos = (0, 100)
node_c.pos = (0, -50)


def print_node_pos(node):
    print('%s Pos: %s' % (str(node), str(node.pos)))


def print_node_selected(node):
    print('%s Selected: %s' % (str(node), str(node.selected)))


def assign_pos_as_label_on_c():
    node_c.label = str(node_c.pos)


def conn_added_cb(source, sink, param):
    print('conn added %s -> %s from %s' % (source, sink, param))


def conn_removed_cb(source, sink, param):
    print('conn removed %s -> %s from %s' % (source, sink, param))

# Can directly listen to nodes
# node_a.pos_changed.connect(
#     lambda: print('Node A Pos: %s (direct)' % str(node_a.pos)))
# node_a.selected_changed.connect(
#     lambda: print('Node A Selected: %s (direct)' % str(node_a.selected)))
graph.node_pos_changed.connect(print_node_pos)
graph.node_selected_changed.connect(print_node_selected)
node_c.pos_changed.connect(assign_pos_as_label_on_c)
# Only one connection_added signal is fired on the graph, but each parameter
# fires its own connection_added.
graph.connection_added.connect(conn_added_cb)
graph.connection_removed.connect(conn_removed_cb)


sys.exit(app.exec_())
