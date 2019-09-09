# -*- coding: utf-8 -*-


debug = False

def print_debug(str):
    if debug:
        print(str)

class TreeNode:
    def __init__(self, classname):
        self.parent = None # class name
        self.interfaces = set() # parent interface of the implemented child class
        self.implements = set() # implement child class of interface
        self.lchild = set() # set of class name, who relied on current class
        self.rchild = set() # set of class name, whom current class is relied on
        self.childs = set() # set of class name, who is inherited from current class
        self.name = classname.strip()
        self.displayname = classname.strip().replace('.', '・').replace('<', '‹').replace('>', '›')

    def is_valid_node(self):
        return True if self.name is not None and len(self.name) > 0 else False

    def is_equal(self, classname):
        return True if classname == self.name else False

    def is_parent(self):
        return True if len(self.childs) > 0 else False

    def is_leaf(self):
        return True if len(self.childs) < 1 else False

    def add_parent(self, parent_class_name):
        # parent class of current class
        self.parent = parent_class_name

    def add_child(self, child_class_name):
        # sometimes we don't know it's left or right child
        self.childs.add(child_class_name)

    def add_interface(self, parent_interface_name):
        self.interfaces.add(parent_interface_name)
    
    def add_implement(self, child_implement_name):
        self.implements.add(child_implement_name)

    def add_lchild(self, child_class_name):
        # classes relied on current class
        self.lchild.add(child_class_name)

    def add_rchild(self, child_class_name):
        # classes whom current class is relied on
        self.rchild.add(child_class_name)

    def is_standalone(self):
        if len(self.childs) > 0 \
                or len(self.lchild) > 0 \
                or len(self.rchild) > 0 \
                or self.parent is not None:
            return False
        else:
            return True

    def get_rootnode(self):
        rootnode = self
        while rootnode.parent is not None:
            rootnode = rootnode.parent
        return rootnode

    def get_node_from_root(self, with_class_name):
        root = self.get_rootnode()
        return root.get_node_from_current(with_class_name)

    def get_node_from_current(self, with_class_name):
        # will goto infinite loop
        # if with_class_name is None or len(with_class_name.strip()) < 1:
        #     return None
        # else:
        #     print_debug('get_node_from_current from ' + self.name + ' for ' + with_class_name)
        # if self.name == with_class_name:
        #     return self
        # elif len(self.lchild) > 0:
        #     for nd in self.lchild:
        #         nd.get_node_from_current(with_class_name)
        # elif len(self.rchild) > 0:
        #     for nd in self.rchild:
        #         nd.get_node_from_current(with_class_name)
        return None

    def is_parent_of_node(self, clz_name):
        return True if self.parent is not None and self.parent == clz_name else False

    def is_child_of_node(self, clz_name):
        return True if len(self.childs) > 0 and clz_name in self.childs else False

    def is_rely_on_node(self, clz_name):
        return True if len(self.lchild) > 0 and clz_name in self.lchild else False

    def is_relied_by_node(self, clz_name):
        return True if len(self.rchild) > 0 and clz_name in self.rchild else False

    def is_clz_direct_relate_with_node(self, clz_name):
        # only check direct childs and parent
        print_debug('node class ' + self.name + ' , class to check ' + clz_name)
        return True if self.is_parent_of_node(clz_name) \
            or self.is_child_of_node(clz_name) \
            or self.is_rely_on_node(clz_name) \
            or self.is_relied_by_node(clz_name) else False

    def is_clz_relate_with_node_in_depth(self, clz_name, depth, dict_classname_treenode):
        if depth == -1:
            return True
        elif depth == 0:
            return False
        else:
            if self.is_equal(clz_name):
                return True
            else:
                if len(self.lchild) > 0:
                    for lc in self.lchild:
                        if lc in dict_classname_treenode.keys():
                            nd = dict_classname_treenode.get(lc)
                            if nd.is_clz_relate_with_node_in_depth(clz_name, depth - 1, dict_classname_treenode):
                                return True
                if len(self.rchild) > 0:
                    for rc in self.rchild:
                        if rc in dict_classname_treenode.keys():
                            nd = dict_classname_treenode.get(rc)
                            if nd.is_clz_relate_with_node_in_depth(clz_name, depth - 1, dict_classname_treenode):
                                return True
        return False


def dump(dict_classname_treenode):
    if dict_classname_treenode is not None and len(dict_classname_treenode) > 0:
        for clz in dict_classname_treenode:
            nd = dict_classname_treenode.get(clz)
            print(nd.name)
            if nd.parent is not None:
                print('\t parent = ' + nd.parent)
            else:
                print('\t parent = none')
            print('\t childs = ' + str(nd.childs))
            print('\t relied by ' + str(nd.lchild))
            print('\t relied on ' + str(nd.rchild))


