from ..signal import Signal
from . import parentChild
from . import parameter


class Node(parentChild.ParentChild):
    def __init__(self, label=None, nodeId=0, parent=None, graph=None):
        super(Node, self).__init__()
        # Simple properties with signals
        self._nodeId = nodeId
        self._label = label
        self._pos = (0, 0)
        self._selected = False
        self._graph = graph
        self._parameters = {}
        self._rootParameter = None

        # Signals
        self.nodeIdChanged = Signal()
        self.labelChanged = Signal()
        self.posChanged = Signal()
        self.selectedChanged = Signal()

        self.attributesChanged = Signal()
        # "attributesChanged" is really one of four other signals
        # TODO: we could change the args into a dict
        self.posChanged.connect(self.attributesChanged.emit)
        self.selectedChanged.connect(self.attributesChanged.emit)
        self.labelChanged.connect(self.attributesChanged.emit)

        # Parameters
        self.parameterAdded = Signal()
        self.parameterRemoved = Signal()

        # Parameter's signals loft up
        self.connectionAdded = Signal()
        self.connectionRemoved = Signal()
        self.parameterSinkChanged = Signal()
        self.parameterSourceChanged = Signal()

        # Connect parameterAdded to callbacks here
        self.parameterAdded.connect(self._parameterAddedCallback)
        self.parameterRemoved.connect(self._parameterRemovedCallback)

        self.parent = parent
        self.acceptsChildren = False
        self.registerCallbacks()
        self._graph.nodeAdded.emit(node=self)

    def delete(self):
        self.parent = None
        self.graph = None

    def __repr__(self):
        # Fake repr for readability
        labelStr = ''
        if self.label is not None:
            labelStr = '/%s' % self.label
        return '<%s: %s%s>' % (self.__class__.__name__, self.nodeId, labelStr)

    def registerCallbacks(self):
        # Graph level signals
        self.posChanged.connect(self.graph.nodePosChanged.emit, node=self)
        self.selectedChanged.connect(self.graph.nodeSelectedChanged.emit,
                                     node=self)
        self.nodeIdChanged.connect(self.graph.nodeIdChanged.emit,
                                   node=self)
        self.labelChanged.connect(self.graph.nodeLabelChanged.emit,
                                  node=self)
        self.parentChanged.connect(self.graph.nodeParentChanged.emit,
                                   node=self)
        self.attributesChanged.connect(self.graph.nodeAttributesChanged.emit,
                                       node=self)

        # lofted parameter signals
        self.connectionAdded.connect(self.graph.connectionAdded.emit)
        self.connectionRemoved.connect(self.graph.connectionRemoved.emit)
        self.parameterSinkChanged.connect(self.graph.parameterSinkChanged.emit)
        self.parameterSourceChanged.connect(
                self.graph.parameterSourceChanged.emit)

    def deregisterCallbacks(self):
        # Graph level signals
        self.posChanged.disconnect(self.graph.nodePosChanged.emit)
        self.selectedChanged.disconnect(self.graph.nodeSelectedChanged.emit)
        self.nodeIdChanged.disconnect(self.graph.nodeIdChanged.emit)
        self.labelChanged.disconnect(self.graph.nodeLabelChanged.emit)
        self.parentChanged.disconnect(self.graph.nodeParentChanged.emit)
        self.attributesChanged.disconnect(
                self.graph.nodeAttributesChanged.emit)

        # lofted parameter signals
        self.connectionAdded.disconnect(self.graph.connectionAdded.emit)
        self.connectionRemoved.disconnect(self.graph.connectionRemoved.emit)
        self.parameterSinkChanged.disconnect(
                self.graph.parameterSinkChanged.emit)
        self.parameterSourceChanged.disconnect(
                self.graph.parameterSourceChanged.emit)

    @property
    def nodeId(self):
        return self._nodeId

    @nodeId.setter
    def nodeId(self, newVal):
        oldNodeId = self._nodeId
        self._nodeId = newVal
        self.nodeIdChanged.emit(oldNodeId=oldNodeId, nodeId=self._nodeId)

    @nodeId.deleter
    def nodeId(self):
        del self._nodeid

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
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, newVal):
        self._pos = newVal
        self.posChanged.emit(pos=self._pos)

    @pos.deleter
    def pos(self):
        del self._pos

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, newVal):
        self._selected = newVal
        self.selectedChanged.emit(selected=self._selected)

    @selected.deleter
    def selected(self):
        del self._selected

    @property
    def rootParameter(self):
        if self._rootParameter is None:
            self._rootParameter = parameter.Parameter(node=self)
        return self._rootParameter

    @rootParameter.setter
    def rootParameter(self, rootParameter):
        # TODO
        return

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, newGraph):
        if self._graph == newGraph:
            return
        self.deregisterCallbacks()
        if self.parent is not None and self.parent.graph != newGraph:
            self.parent = None
        self._graph.nodeRemoved.emit(node=self)
        self._graph = newGraph
        if self._graph is not None:
            self.registerCallbacks()
            self._graph.nodeAdded.emit(node=self)

    @property
    def parameters(self):
        return list(self._parameters.values())

    def getParameter(self, paramId):
        return self._parameters.get(paramId, None)

    def __getitem__(self, paramId):
        return self.getParameter(paramId)

    @parameters.setter
    def parameters(self, newParams):
        # TODO
        return

    @property
    def acceptsChildren(self):
        return False

    @parentChild.ParentChild.acceptsChildren.setter
    def acceptsChildren(self, acceptsChildren):
        # I don't care what you give me, I don't accept children.
        parentChild.ParentChild.acceptsChildren.fset(self, False)

    def createParameter(self, *args, **kwargs):
        kwargs['node'] = self
        return parameter.Parameter(*args, **kwargs)

    def deleteParameter(self, parameter):
        parameter.delete()

    def _parameterAddedCallback(self, parameter):
        if parameter.parameterId in self._parameters:
            parameter.parameterId = self._uniquefyParameterId(
                    parameter.parameterId)
        self._parameters[parameter.parameterId] = parameter

    def _parameterRemovedCallback(self, parameter):
        if param.parameterId in self._parameters:
            del self._parameters[param.parameterId]

    def _uniquefyParameterId(self, paramId):
        if not paramId not in self._parameters:
            return paramId
        # The ParamID can be either a string or int (or anything else you want,
        # but we need to be able to make a unique type)
        if type(paramId) == type(str):
            attempt = 0
            uniqueId = paramId
            while uniqueId in self._parameters:
                attempt += 1
                uniqueId = paramId + '_' + str(attempt)
            return uniqueId

        elif type(paramId) == type(int) or type(paramId) == type(float):
            while uniqueId in self._parameters:
                uniqueId += 1
            return uniqueId

        print('Warning! Unable to unquefy nodeId type %s' % str(type(nodeId)))
        return paramId


class SubgraphNode(Node):
    def __init__(self, *args, **kwargs):
        super(SubgraphNode, self).__init__(*args, **kwargs)
        self.acceptsChildren = True
        self._tunnelParameters = {}
        self._parameterToTunnel = {}
        self._tunnelToParameter = {}

    @property
    def acceptsChildren(self):
        return True

    @parentChild.ParentChild.acceptsChildren.setter
    def acceptsChildren(self, acceptsChildren):
        # I don't care what you give me, I always accept children.
        parentChild.ParentChild.acceptsChildren.fset(self, True)

    def _parameterAddedCallback(self, param):
        # This is pretty dirty, TODO: clean up
        if (param.parameterId in self._parameters or
                param.parameterId in self._tunnelParameters):
            param.parameterId = self._uniquefyParameterId(param.parameterId)

        if isinstance(param, parameter.TunnelParameter):
            self._tunnelParameters[param.parameterId] = param
        else:
            super(SubgraphNode, self)._parameterAddedCallback(param)
            tunnel = parameter.TunnelParameter(parameter=param)
            self._parameterToTunnel[param] = tunnel
            self._tunnelToParameter[tunnel] = param

    def _parameterRemovedCallback(self, param):
        # This is pretty dirty, TODO: clean up
        if isinstance(param, parameter.TunnelParameter):
            if param.parameterId in self._tunnelParameters:
                del self._tunnelParameters[param.parameterId]
                if param in self._tunnelToParameter:
                    self._tunnelToParameter[param].node = None
        else:
            tunnelParam = self.getTunnelParameter(param)
            tunnelParam.node = None
            tunnelParam.tunneledParameter = None
            super(SubgraphNode, self)._parameterAddedCallback(param)
            del self._parameterToTunnel[param]
            del self._tunnelToParameter[tunnelParam]

    def getTunnelParameter(self, param):
        return self._parameterToTunnel.get(param, None)

    def getParameterForTunnel(self, tunnel):
        return self._tunnelToParameter.get(tunnel, None)

    @property
    def tunnelParameters(self):
        return list(self._tunnelParameters.values())
