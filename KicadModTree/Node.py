'''
kicad-footprint-generator is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

kicad-footprint-generator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kicad-footprint-generator. If not, see < http://www.gnu.org/licenses/ >.

(C) 2016 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
'''

from copy import deepcopy

from .Point import *


class Node(object):
    def __init__(self):
        self._parent = None
        self._childs = []


    def append(self, node):
        '''
        add node to child
        '''
        if not isinstance(node, Node):
            raise Exception('invalid object, has to be based on Node')

        self._childs.append(node)

        if node._parent:
            raise Exception('muliple parents are not allowed!')
        node._parent = self


    def extend(self, nodes):
        '''
        add list of nodes to child
        '''
        for node in nodes:
            self.append(node)


    def remove(self, node):
        '''
        remove child from node
        '''
        while self._childs.count(node):
            self._childs.remove(node)

        node._parent = None


    def insert(self, node):
        '''
        moving all childs into the node, and using the node as new parent of those childs
        '''
        if not isinstance(node, Node):
            raise Exception('invalid object, has to be based on Node')

        for child in self._childs.copy():
            self.remove(child)
            node.append(child)

        self.append(node)


    def copy(self):
        copy = deepcopy(self)
        copy._parent = None
        return copy


    def getChilds(self):
        '''
        Get all childs of this node
        '''
        return self._childs


    def getVirtualChilds(self):
        '''
        Get all childs of this node including the childs which are generated by nodes
        '''
        return self.getChilds()


    def getParent(self):
        '''
        get Parent Node of this Node
        '''
        return self._parent


    def getRootNode(self):
        '''
        get Root Node of this Node
        '''

        # TODO: recursion detection

        if not self.getParent():
            return self

        return self.getParent().getRootNode()


    def renderList(self):
        '''
        return a list of render strings which are required to create a file
        '''
        render_list = []

        # TODO: recursion detection

        for child in self.getVirtualChilds():
            child_render_list = child.renderList()
            if type(child_render_list) is list and len(child_render_list):
                render_list.extend(child_render_list)
        return render_list


    def getRealPosition(self, coordinate):
        '''
        return position of point after applying all transformation and rotation operations
        '''
        if not self._parent:
            return Point(coordinate)

        return self._parent.getRealPosition(coordinate)


    def calculateOutline(self, outline=None):
        min_x, min_y = 0, 0
        max_x, max_y = 0, 0

        if outline:
            min_x = outline['min']['x']
            min_y = outline['min']['y']
            max_x = outline['max']['x']
            max_y = outline['max']['y']

        for child in self.getVirtualChilds():
            child_outline = child.calculateOutline()

            min_x = min([min_x, child_outline['min']['x']])
            min_y = min([min_y, child_outline['min']['y']])
            max_x = max([max_x, child_outline['max']['x']])
            max_y = max([max_y, child_outline['max']['y']])

        return {'min':PointXY(min_x, min_y), 'max':PointXY(max_x, max_y)}


    def _getRenderTreeText(self):
        '''
        Text which is displayed when generating a render tree
        '''
        return type(self).__name__


    def _getRenderTreeSymbol(self):
        '''
        Symbol which is displayed when generating a render tree
        '''
        if self._parent is None:
            return "+"

        return "*"


    def getRenderTree(self, rendered_nodes=None):
        '''
        print render tree
        '''
        if rendered_nodes is None:
            rendered_nodes = set()

        if self in rendered_nodes:
            raise Exception('recursive definition of render tree!')

        rendered_nodes.add(self)

        tree_str = "{0} {1}".format(self._getRenderTreeSymbol(), self._getRenderTreeText())
        for child in self.getChilds():
            tree_str += '\r\n  '
            tree_str += '  '.join(child.getRenderTree(rendered_nodes).splitlines(True))

        return tree_str


    def getVirtualRenderTree(self, rendered_nodes=None):
        '''
        print virtual render tree
        '''
        if rendered_nodes is None:
            rendered_nodes = set()

        if self in rendered_nodes:
            raise Exception('recursive definition of render tree!')

        rendered_nodes.add(self)

        tree_str = "{0} {1}".format(self._getRenderTreeSymbol(), self._getRenderTreeText())
        for child in self.getVirtualChilds():
            tree_str += '\r\n  '
            tree_str += '  '.join(child.getVirtualRenderTree(rendered_nodes).splitlines(True))

        return tree_str
