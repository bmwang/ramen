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

assert(nodegraph.getNodeUI(node_a) is not None)
assert(nodegraph.getNodeUI(node_b) is not None)

node_a.pos = (0, 0)
node_b.pos = (0, 50)
node_c.pos = (0, -50)


def print_node_pos(node):
    print('%s Pos: %s' % (str(node), str(node.pos)))


def print_node_selected(node):
    print('%s Selected: %s' % (str(node), str(node.selected)))


def assign_pos_as_label_on_c():
    node_c.label = str(node_c.pos)

# Can directly listen to nodes
# node_a.pos_changed.connect(
#     lambda: print('Node A Pos: %s (direct)' % str(node_a.pos)))
# node_a.selected_changed.connect(
#     lambda: print('Node A Selected: %s (direct)' % str(node_a.selected)))
graph.node_pos_changed.connect(print_node_pos)
graph.node_selected_changed.connect(print_node_selected)
node_c.pos_changed.connect(assign_pos_as_label_on_c)

sys.exit(app.exec_())
