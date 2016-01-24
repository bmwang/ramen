from PyQt4 import QtGui, QtCore
import ramen
from ramen.core.signal import Signal


class NodegraphScene(QtGui.QGraphicsScene):
    def __init__(self, subgraphNodeUI, parent=None):
        super(NodegraphScene, self).__init__(parent)
        self._subgraphNodeUI = subgraphNodeUI
        self.setBackgroundBrush(QtGui.QColor(50, 50, 50))

        self._activeDrag = False
        self._dragGroup = QtGui.QGraphicsItemGroup(scene=self)
        self._dragGroup.setHandlesChildEvents(False)

        # 'band select' for banding selection
        # anchor for a rect corner
        self._bandSelectAnchor = None
        # the actual rect to show
        self._bandSelectRect = self.addRect(0, 0, 0, 0)
        self._bandSelectRect.setVisible(False)
        self._bandSelectRect.setPen(
                QtGui.QPen(QtGui.QColor(255, 255, 255)))
        self._bandSelectRect.setBrush(
                QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        self._bandSelectRect.setOpacity(0.25)

        # mouse connection for when a user creates a connection
        self.mousePosChanged = Signal()
        self.mousePos = QtCore.QPointF()
        self.mouseConnection = None

    @property
    def activeDrag(self):
        return self._activeDrag

    @activeDrag.setter
    def activeDrag(self, val):
        # XXX should i really be using a property setter in a subclass
        # of a library that doesn't?
        if val == self.activeDrag:
            return
        if val:
            # Grab all the selected nodes and put them into a drag group
            # so that we can just drag one item instead of many
            self._activeDrag = True
            self._dragGroup.setPos(0, 0)
            for node in self.graph.selected_nodes:
                self._dragGroup.addToGroup(self.nodegraph.getNodeUI(node))
        else:
            # Stamp the drag group back into the scene
            self._activeDrag = False
            for childNodeUI in self._dragGroup.childItems():
                newPos = childNodeUI.mapToScene(QtCore.QPointF(0, 0))
                childNodeUI.setParentItem(None)
                childNodeUI.node.pos = (newPos.x(), newPos.y())

    @property
    def graph(self):
        return self._subgraphNodeUI.node.graph

    @property
    def nodegraph(self):
        return self._subgraphNodeUI.nodegraph

    def itemsTypeAt(self, pos, itemType):
        # Convenience function -- may remove later
        for item in self.items(pos):
            if isinstance(item, itemType):
                yield item

    def itemTypeAt(self, pos, itemType):
        # Convenience function -- may remove later
        item = None
        try:
            item = self.itemsTypeAt(pos, itemType).next()
        except StopIteration:
            pass
        return item

    def mouseMoveEvent(self, event):
        super(NodegraphScene, self).mouseMoveEvent(event)
        self.mousePos = event.scenePos()
        lastX = event.lastScenePos().x()
        lastY = event.lastScenePos().y()
        curX = event.scenePos().x()
        curY = event.scenePos().y()

        if self.activeDrag:
            # If we're dragging something, move the drag group
            dragGroup = self._dragGroup
            dragX = dragGroup.pos().x()
            dragY = dragGroup.pos().y()
            dragGroup.setPos(dragX + (curX - lastX), dragY + (curY - lastY))
            for childNodeUI in self._dragGroup.childItems():
                # move this into nodeui?
                childNodeUI.updatedGeo.emit()
        elif self._bandSelectAnchor is not None:
            # If we created a band selection anchor, create/update
            # a rect to show the selection area accordingly
            rectX = self._bandSelectAnchor.x()
            rectY = self._bandSelectAnchor.y()
            if not self._bandSelectRect.isVisible():
                self._bandSelectRect.show()
            rect = QtCore.QRectF(min(rectX, curX), min(rectY, curY),
                                 abs(rectX - curX), abs(rectY - curY))
            self._bandSelectRect.setRect(rect)

        self.mousePosChanged.emit()

    def mouseReleaseEvent(self, event):
        # Stop an active drag
        self.activeDrag = False
        if self._bandSelectAnchor is not None:
            # If we had a band select anchor, hide it.
            event.accept()
            self.graph.selected_nodes = []
            for uiItem in self.collidingItems(self._bandSelectRect):
                if isinstance(uiItem, ramen.editor.qt.nodegraph.Node):
                    uiItem.node.selected = True
            self._bandSelectRect.hide()
            self._bandSelectAnchor = None
        super(NodegraphScene, self).mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        super(NodegraphScene, self).mouseDoubleClickEvent(event)
        hoveredNodeUI = self.itemTypeAt(event.scenePos(),
                                        ramen.editor.qt.nodegraph.Node)
        if hoveredNodeUI is not None:
            hoveredNodeUI.node.selected = True

    def mousePressEvent(self, event):
        super(NodegraphScene, self).mousePressEvent(event)
        if not event.isAccepted():
            if event.buttons() == QtCore.Qt.LeftButton:
                event.accept()
                hoveredNodeUI = self.itemTypeAt(event.scenePos(),
                                                ramen.editor.qt.nodegraph.Node)
                if hoveredNodeUI is not None:
                    hoveredParamUI = self.itemTypeAt(
                        event.scenePos(),
                        ramen.editor.qt.nodegraph.Parameter)
                    if hoveredParamUI is not None and not self.activeDrag:
                        hoveredParam = hoveredParamUI.ramenParameter
                        if self.mouseConnection is None:
                            self.createMouseConnection(hoveredParam)
                        else:
                            self.sinkMouseConnection(hoveredParam)
                    else:
                        # If we clicked directly on a node
                        hoveredNode = hoveredNodeUI.node
                        if event.modifiers() == QtCore.Qt.ShiftModifier:
                            # Shift modifier acts as a not, and we dont drag
                            hoveredNode.selected = not hoveredNode.selected
                        else:
                            if not hoveredNode.selected:
                                # If this node wasn't selected, select it
                                self.graph.selected_nodes = []
                                hoveredNode.selected = True
                            # Drag if this node was clicked without a modifier
                            self.activeDrag = True
                else:
                    self._bandSelectAnchor = event.scenePos()
                    self._bandSelectRect.setRect(QtCore.QRectF(
                        self._bandSelectAnchor, self._bandSelectAnchor))

                    if self.mouseConnection is None:
                        hoveredConnUI = self.itemTypeAt(
                            event.scenePos(),
                            ramen.editor.qt.nodegraph.Connection)
                        if hoveredConnUI is not None:
                            sourceVec = (hoveredConnUI.sourcePos -
                                         event.scenePos())
                            sinkVec = hoveredConnUI.sinkPos - event.scenePos()
                            # manhattan distance
                            sourceDist = abs(sourceVec.x())+abs(sourceVec.y())
                            sinkDist = abs(sinkVec.x())+abs(sinkVec.y())
                            farthestParam = hoveredConnUI.source
                            if sourceDist < sinkDist:
                                farthestParam = hoveredConnUI.sink
                            hoveredConnUI.source.disconnect(hoveredConnUI.sink)
                            self.createMouseConnection(farthestParam)
                    else:
                        self.sinkMouseConnection(None)

    def createMouseConnection(self, param):
        if param.source:
            self.mouseConnection = ramen.editor.qt.nodegraph.MouseConnection(
                nodegraph=self.nodegraph,
                sourceParam=param)
        elif param.sink:
            self.mouseConnection = ramen.editor.qt.nodegraph.MouseConnection(
                nodegraph=self.nodegraph,
                sinkParam=param)

    def sinkMouseConnection(self, param):
        if param is not None:
            self.mouseConnection.anchorParameter.connect(param)
        self.removeItem(self.mouseConnection)
        self.mouseConnection = None
