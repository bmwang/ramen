# Quick tests just as I go -- formalize and make full coverage later

import ramen
graph = ramen.Graph()


class Scope(object):
    pass

# One child
node = ramen.node.Node(graph=graph)
assert(not node.accepts_children)
assert(node.parent == graph.root_node)
assert(node in graph.root_node.children)
assert(len(graph.root_node.children) == 1)

node = ramen.node.SubgraphNode(graph=graph)
assert(node.accepts_children)

# Ten children
graph.clear()
# After a clear, there is at least the root node
assert(len(graph.nodes) == 1)
for i in range(10):
    ramen.node.Node(graph=graph)
assert(len(graph.nodes) == 11)
assert(len(graph.root_node.children) == 10)

# Deep children
graph.clear()
assert(len(graph.nodes) == 1)
last_node = None
for i in range(10):
    last_node = ramen.node.SubgraphNode(graph=graph, parent=last_node)
assert(len(graph.nodes) == 11)
assert(len(graph.root_node.children) == 1)
last_node = graph.root_node
for i in range(10):
    assert(len(last_node.children) == 1)
    last_node = last_node.children.pop()
assert(len(last_node.ancestors) == 10)
# reparent
last_node.ancestors = [graph.root_node,
                       graph.root_node.children.pop().children.pop()]
assert(len(last_node.ancestors) == 2)
assert(len(last_node.parent.children) == 2)

#  node_id callbacks
# TODO more callback tests
graph.clear()
node = ramen.node.Node(graph=graph)

scope = Scope()
scope.test = False


def callback_test():
    scope.test = True
node.node_id_changed.connect(callback_test)
node.node_id = graph._uniquefy_node_id(node.node_id)
assert(scope.test)
assert(len(graph.nodes) == 2)

# parameters
graph.clear()
node_a = ramen.node.Node(graph=graph)
node_b = ramen.node.Node(graph=graph)
node_c = graph.create_node()

param_a = ramen.node.Parameter('param a', node=node_a)
param_b = ramen.node.Parameter('param b', node=node_b)
param_c = node_c.create_parameter('param c')

param_a.source = True
param_b.source = True
param_b.sink = True
param_c.sink = True

param_a.connect(param_b)
param_b.connect(param_c)

assert(param_b in param_a.connections)
assert(param_b in param_a.connections_out)
assert(param_b not in param_a.connections_in)

assert(param_a in param_b.connections)
assert(param_a not in param_b.connections_out)
assert(param_a in param_b.connections_in)

assert(param_c in param_b.connections)
assert(param_c in param_b.connections_out)
assert(param_c not in param_b.connections_in)

assert(param_a not in param_c.connections)
assert(param_c not in param_a.connections)


# Connecting parameters of different subgraphs
# root
# |\
# A B
# | |\
# C D E
#   |
#   F
# Connecting a parameter on C to F should create tunnel parameters on A,B,D
graph.clear()
node_a = ramen.node.SubgraphNode(graph=graph, label='a')
node_b = ramen.node.SubgraphNode(graph=graph, label='b')
node_c = ramen.node.Node(graph=graph, parent=node_a, label='c')
node_d = ramen.node.SubgraphNode(graph=graph, parent=node_b, label='d')
node_e = ramen.node.Node(graph=graph, parent=node_b, label='e')
node_f = ramen.node.Node(graph=graph, parent=node_d, label='f')

param_c = ramen.node.Parameter(node=node_c, label='c')
param_c.source = True
param_f = ramen.node.Parameter(node=node_f, label='f')
param_f.sink = True
param_c.connect(param_f)

assert(len(graph.root_node.parameters) == 0)
assert(len(node_a.parameters) == 1)
assert(len(node_b.parameters) == 1)
assert(len(node_c.parameters) == 1)
assert(len(node_d.parameters) == 1)
assert(len(node_e.parameters) == 0)
assert(len(node_f.parameters) == 1)

assert(param_c in
       node_a.get_tunnel_parameter(node_a.parameters[0]).connections)
assert(node_a.get_tunnel_parameter(node_a.parameters[0]) in
       param_c.connections)
assert(node_a.parameters[0] in node_b.parameters[0].connections)
assert(node_b.parameters[0] in node_a.parameters[0].connections)
assert(node_d.parameters[0] in node_b.tunnel_parameters[0].connections)
assert(node_b.tunnel_parameters[0] in node_d.parameters[0].connections)
assert(param_f in node_d.tunnel_parameters[0].connections)
assert(node_d.tunnel_parameters[0] in param_f.connections)

# Connecting a parameter on E to F should not create an additional tunnel
# parameter on D
param_e = ramen.node.Parameter(node=node_e, label='e')
param_e.source = True
param_e.connect(param_f)
assert(len(node_d.parameters) == 1)
assert(len(node_d.parameters[0].connections) == 2)
