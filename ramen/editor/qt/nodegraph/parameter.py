from PyQt4 import QtGui, QtCore
from ramen.editor.qt.nodegraph.nodegraphscene import NodegraphScene


class Parameter(QtGui.QGraphicsItem):
    def __init__(self, nodegraph, ramenParameter, *args, **kwargs):
        kwargs['scene'] = nodegraph.getNodeUI(ramenParameter.node).scene()
        super(Parameter, self).__init__(*args, **kwargs)
        self._nodegraph = nodegraph
        self._ramenParameter = ramenParameter
        self._label = QtGui.QGraphicsTextItem(self)

        self.registerRamenCallbacks()
        self.updateGeo()

    @property
    def nodegraph(self):
        return self._nodegraph

    @property
    def ramenParameter(self):
        return self._ramenParameter

    def registerRamenCallbacks(self):
        pass

    def deregisterRamenCallbacks(self):
        pass

    def updateGeo(self):
        nodeUI = self.nodegraph.getNodeUI(self.ramenParameter.node)

        boundingRect = QtCore.QRectF()
        self._label.setDefaultTextColor(QtGui.QColor(255, 255, 255, 150))
        if self.ramenParameter.parent is None:
            self._label.setPlainText('')
        else:
            self._label.setPlainText(self.ramenParameter.label)
            boundingRect |= self._label.boundingRect().translated(
                    self._label.pos())
        for childParameter in self.ramenParameter.children:
            childParameterUI = nodeUI.getParameterUI(childParameter)
            childParameterUI.setPos(0, boundingRect.height())
            boundingRect |= childParameterUI.boundingRect().translated(
                    childParameterUI.pos())

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, *args):
        pass
