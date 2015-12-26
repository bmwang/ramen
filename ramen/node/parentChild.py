from ..signal import Signal
import itertools


class ParentChild(object):
    '''An object with parent, child relationships'''
    def __init__(self):
        self._parent = None
        self._children = set()
        self._accepts_children = True

        self.accepts_children_changed = Signal()
        self.parent_changed = Signal()
        self.child_added = Signal()
        self.child_removed = Signal()
        self.children_changed = Signal()

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if parent == self._parent:
            return
        if parent is not None and not parent.accepts_children:
            return

        if self._parent is not None:
            self._parent.disown_child(self)
            self._parent = None

        self._parent = parent
        if parent is not None:
            parent.adopt_child(self)
        self.parent_changed.emit(parent=parent)

    @property
    def ancestors(self):
        res = []
        curItem = self
        while curItem.parent is not None:
            res.append(curItem.parent)
            curItem = curItem.parent
        return res

    @ancestors.setter
    def ancestors(self, new_ancestors):
        # This is basically calling parent.setter on everything in the list
        new_ancestors = [None] + new_ancestors + [self]

        def pairwise(iterable):
            # TODO: stick this somewhere better
            a, b = itertools.tee(iterable)
            next(b, None)
            return zip(a, b)
        for parent, child in pairwise(new_ancestors):
            child.parent = parent

    @property
    def children(self):
        # explicitly copy for now
        # TODO: make this work with .add, and etc
        return set(self._children)

    @children.setter
    def children(self, new_children):
        children_to_adopt = new_children.difference(self._children)
        children_to_disown = self._children.difference(new_children)
        if self.accepts_children:
            for child in children_to_adopt:
                self.adopt_child(child)
        for child in children_to_disown:
            self.disown_child(child)

    @property
    def accepts_children(self):
        return self._accepts_children

    @accepts_children.setter
    def accepts_children(self, accepts_children):
        self._accepts_children = accepts_children
        self.accepts_children_changed.emit(accepts_children=accepts_children)

    def adopt_child(self, child):
        if not self.accepts_children:
            return
        if child in self._children:
            return
        self._children.add(child)
        child.parent = self
        self.child_added.emit(child=child)

    def disown_child(self, child):
        if child not in self._children:
            return
        self._children.remove(child)
        child.parent = None
        self.child_removed.emit(child=child)
