from ..signal import Signal
import itertools

class ParentChild(object):
    '''An object with parent, child relationships'''
    def __init__(self):
        self._parent = None
        self._children = set()
        self._acceptsChildren = True

        self.acceptsChildrenChanged = Signal()
        self.parentChanged = Signal()
        self.childAdded = Signal()
        self.childRemoved = Signal()
        self.childrenChanged = Signal()

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if parent == self._parent:
            return
        if parent is not None and not parent.acceptsChildren:
            return

        if self._parent is not None:
            self._parent.disownChild(self)
            self._parent = None

        self._parent = parent
        if parent is not None:
            parent.adoptChild(self)
        self.parentChanged.emit(parent=parent)

    @property
    def ancestors(self):
        res = []
        curItem = self
        while curItem.parent is not None:
            res.append(curItem.parent)
            curItem = curItem.parent
        return res

    @ancestors.setter
    def ancestors(self, newAncestors):
        # This is basically calling parent.setter on everything in the list
        newAncestors = [None] + newAncestors + [self]
        def pairwise(iterable):
            # TODO: stick this somewhere better
            a, b = itertools.tee(iterable)
            next(b, None)
            return zip(a,b)
        for parent, child in pairwise(newAncestors):
            child.parent = parent

    @property
    def children(self):
        # explicitly copy for now
        # TODO: make this work with .add, and etc
        return set(self._children)

    @children.setter
    def children(self, newChildren):
        childrenToAdopt = newChildren.difference(self._children)
        childrenToDisown = self._children.difference(newChildren)
        if self.acceptsChildren:
            for child in childrenToAdopt:
                self.adoptChild(child)
        for child in childrenToDisown:
            self.disownChild(child)

    @property
    def acceptsChildren(self):
        return self._acceptsChildren

    @acceptsChildren.setter
    def acceptsChildren(self, acceptsChildren):
        self._acceptsChildren = acceptsChildren
        self.acceptsChildrenChanged.emit(acceptsChildren=acceptsChildren)

    def adoptChild(self, child):
        if not self.acceptsChildren:
            return
        if child in self._children:
            return
        self._children.add(child)
        child.parent = self
        self.childAdded.emit(child=child)

    def disownChild(self, child):
        if child not in self._children:
            return
        self._children.remove(child)
        child.parent = None
        self.childRemoved.emit(child=child)
