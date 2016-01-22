from PyQt4 import QtGui, QtCore
from ramen.signal import Signal


class Connection(QtGui.QGraphicsPathItem):
    def __init__(self, nodegraph, sourceParam, sinkParam, *args, **kwargs):
        # Infer scene
        if sourceParam is not None and sourceParam.node.parent is not None:
            kwargs['scene'] = nodegraph.getNodeUI(sourceParam.node).scene()
        elif sinkParam is not None and sinkParam.node.parent is not None:
            kwargs['scene'] = nodegraph.getNodeUI(sinkParam.node).scene()
        super(Connection, self).__init__(*args, **kwargs)
        # nodegraph/ramen stuff
        self.nodegraph = nodegraph
        self.source = sourceParam
        self.sink = sinkParam

        # signals
        self.updatedGeo = Signal()
        self.posChanged = Signal()

        # ui stuff
        self.setZValue(-1)
        pen = QtGui.QPen()
        pen.setWidth(0)
        pen.setColor(QtGui.QColor(0, 0, 0, 0))
        self.setPen(pen)

        self._curvePath = QtGui.QPainterPath()
        self._stroker = QtGui.QPainterPathStroker()
        self._selectStroker = QtGui.QPainterPathStroker()
        self._path = QtGui.QPainterPath()
        self._selectPath = QtGui.QPainterPath()
        self.width = 3
        self.registerRamenCallbacks()
        self.registerNodegraphCallbacks()
        self.updateGeo()

    def registerRamenCallbacks(self):
        pass

    def registerNodegraphCallbacks(self):
        # TODO create faster lighterweight self.updatePos
        self.sourceNodeUI.updatedGeo.connect(self.updateGeo)
        self.sinkNodeUI.updatedGeo.connect(self.updateGeo)

    def deregisterRamenCallbacks(self):
        pass

    def deregisterNodegraphCallbacks(self):
        self.sourceNodeUI.updatedGeo.disconnect(self.updateGeo)
        self.sinkNodeUI.updatedGeo.disconnect(self.updateGeo)

    @property
    def sourceNodeUI(self):
        return self.nodegraph.getNodeUI(self.source.node)

    @property
    def sinkNodeUI(self):
        return self.nodegraph.getNodeUI(self.sink.node)

    @property
    def sourceUI(self):
        return self.sourceNodeUI.getParameterUI(self.source)

    @property
    def sinkUI(self):
        return self.sinkNodeUI.getParameterUI(self.sink)

    @property
    def sourcePos(self):
        return self.sourceUI.mapToScene(QtCore.QPointF(
            self.sourceNodeUI.boundingRect().width(),
            self.sourceUI.boundingRect().height()/2))

    @property
    def sinkPos(self):
        return self.sinkUI.mapToScene(QtCore.QPointF(
            0,
            self.sinkUI.boundingRect().height()/2))

    @property
    def sourceColor(self):
        return QtGui.QColor(255, 255, 255)

    @property
    def sinkColor(self):
        return QtGui.QColor(255, 255, 255)

    def updateGeo(self):
        self._stroker.setWidth(self.width)
        self._selectStroker.setWidth(self.width*3)

        gradient = QtGui.QLinearGradient(self.sourcePos, self.sinkPos)
        gradient.setColorAt(0, self.sourceColor)
        gradient.setColorAt(1, self.sinkColor)
        brush = QtGui.QBrush(gradient)
        self.setBrush(brush)

        horizDistance = abs(self.sourcePos.x() - self.sinkPos.x())
        ctrlPointDelta = QtCore.QPointF(horizDistance/4.0, 0)

        self._curvePath = QtGui.QPainterPath(self.sourcePos)
        self._curvePath.cubicTo(self.sourcePos + ctrlPointDelta,
                                self.sinkPos - ctrlPointDelta,
                                self.sinkPos)

        path = self._stroker.createStroke(self._curvePath)

        self.setPath(path)
        self._selectPath = self._selectStroker.createStroke(self._curvePath)
        self.updatedGeo.emit()

    def shape(self):
        return self._selectPath

    def delete(self):
        self.deregisterRamenCallbacks()
        self.deregisterNodegraphCallbacks()
        return self.scene().removeItem(self)


class MouseConnection(Connection):
    def __init__(self, nodegraph, sourceParam=None, sinkParam=None,
                 *args, **kwargs):
        super(MouseConnection, self).__init__(nodegraph, sourceParam,
                                              sinkParam, *args, **kwargs)
        self.registerNodegraphCallbacks()

    def registerNodegraphCallbacks(self):
        self.scene().mousePosChanged.connect(self.updateGeo)

    @property
    def anchorParameter(self):
        if self.source is None:
            return self.sink
        return self.source

    @property
    def sourceUI(self):
        if self.source is None:
            return None
        return Connection.sourceUI.fget(self)

    @property
    def sinkUI(self):
        if self.sink is None:
            return None
        return Connection.sinkUI.fget(self)

    @property
    def mousePos(self):
        if self.scene() is not None:
            return self.scene().mousePos
        return QtCore.QPointF(0, 0)

    @property
    def sourcePos(self):
        if self.sourceUI is None:
            return self.mousePos
        return Connection.sourcePos.fget(self)

    @property
    def sinkPos(self):
        if self.sinkUI is None:
            return self.mousePos
        return Connection.sinkPos.fget(self)
