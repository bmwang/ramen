# Quick tests just as I go -- formalize and make full coverage later

import ramen
graph = ramen.Graph()

# One child
node = ramen.node.Node(graph=graph)
assert(not node.acceptsChildren)
assert(node.parent == graph.rootNode)
assert(node in graph.rootNode.children)
assert(len(graph.rootNode.children) == 1)

node = ramen.node.SubgraphNode(graph=graph)
assert(node.acceptsChildren)

# Ten children
graph.clear()
# After a clear, there is at least the root node
assert(len(graph.nodes) == 1)
for i in range(10):
    ramen.node.Node(graph=graph)
assert(len(graph.nodes) == 11)
assert(len(graph.rootNode.children) == 10)

# Deep children
graph.clear()
assert(len(graph.nodes) == 1)
lastNode = None
for i in range(10):
    lastNode = ramen.node.SubgraphNode(graph=graph, parent=lastNode)
assert(len(graph.nodes) == 11)
assert(len(graph.rootNode.children) == 1)
lastNode = graph.rootNode
for i in range(10):
    assert(len(lastNode.children) == 1)
    lastNode = lastNode.children.pop()
assert(len(lastNode.ancestors) == 10)
# reparent
lastNode.ancestors = [graph.rootNode,
        graph.rootNode.children.pop().children.pop()]
assert(len(lastNode.ancestors) == 2)
assert(len(lastNode.parent.children) == 2)

#  nodeId callbacks
# TODO more callback tests
graph.clear()
node = ramen.node.Node(graph=graph)
curNodeId = node.nodeId
class Scope(object): pass
scope = Scope()
scope.test = False
def callbackTest():
    scope.test = True
node.nodeIdChanged.connect(callbackTest)
node.nodeId = graph._uniquefyNodeId(node.nodeId)
assert(scope.test)
assert(len(graph.nodes) == 2)

# parameters
graph.clear()
nodeA = ramen.node.Node(graph=graph)
nodeB = ramen.node.Node(graph=graph)
nodeC = graph.createNode()

paramA = ramen.node.Parameter('paramLabelA', node=nodeA)
paramB = ramen.node.Parameter('paramLabelB', node=nodeB)
paramC = nodeC.createParameter('paramLabelC')

paramA.source = True
paramB.source = True
paramB.sink = True
paramC.sink = True

paramA.connect(paramB)
paramB.connect(paramC)

assert(paramB in paramA.connections)
assert(paramB in paramA.connectionsOut)
assert(paramB not in paramA.connectionsIn)

assert(paramA in paramB.connections)
assert(paramA not in paramB.connectionsOut)
assert(paramA in paramB.connectionsIn)

assert(paramC in paramB.connections)
assert(paramC in paramB.connectionsOut)
assert(paramC not in paramB.connectionsIn)

assert(paramA not in paramC.connections)
assert(paramC not in paramA.connections)


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
nodeA = ramen.node.SubgraphNode(graph=graph, label='a')
nodeB = ramen.node.SubgraphNode(graph=graph, label='b')
nodeC = ramen.node.Node(graph=graph, parent=nodeA, label='c')
nodeD = ramen.node.SubgraphNode(graph=graph, parent=nodeB, label='d')
nodeE = ramen.node.Node(graph=graph, parent=nodeB, label='e')
nodeF = ramen.node.Node(graph=graph, parent=nodeD, label='f')

paramC = ramen.node.Parameter(node=nodeC, label='c')
paramC.source = True
paramF = ramen.node.Parameter(node=nodeF, label='f')
paramF.sink = True
paramC.connect(paramF)

assert(len(graph.rootNode.parameters) == 0)
assert(len(nodeA.parameters) == 1)
assert(len(nodeB.parameters) == 1)
assert(len(nodeC.parameters) == 1)
assert(len(nodeD.parameters) == 1)
assert(len(nodeE.parameters) == 0)
assert(len(nodeF.parameters) == 1)

assert(paramC in nodeA.getTunnelParameter(nodeA.parameters[0]).connections)
assert(nodeA.getTunnelParameter(nodeA.parameters[0]) in paramC.connections)
assert(nodeA.parameters[0] in nodeB.parameters[0].connections)
assert(nodeB.parameters[0] in nodeA.parameters[0].connections)
assert(nodeD.parameters[0] in nodeB.tunnelParameters[0].connections)
assert(nodeB.tunnelParameters[0] in nodeD.parameters[0].connections)
assert(paramF in nodeD.tunnelParameters[0].connections)
assert(nodeD.tunnelParameters[0] in paramF.connections)

# Connecting a parameter on E to F should not create an additional tunnel
# parameter on D
paramE = ramen.node.Parameter(node=nodeE, label='e')
paramE.source = True
paramE.connect(paramF)
assert(len(nodeD.parameters) == 1)
assert(len(nodeD.parameters[0].connections) == 2)
