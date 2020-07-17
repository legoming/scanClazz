# -*- coding: utf-8 -*-


debug = False

gClassnameSet = set()
gClassDefinedFileSet = set()
gDic_Classname_File = {}
gDic_File_ClassnameSet = {} # 1 file can define several classes

def print_debug(str):
    if debug:
        print(str)

class TreeNode:
    def __init__(self, classname, file, ns=''):
        global gClassnameSet
        global gClassDefinedFileSet
        global gDic_Classname_File
        global gDic_File_ClassnameSet
        if len(ns) > 0 and ns.find(r'.') > 0:
            self.id = ns + '.' + classname # class name with package / namespace
        elif len(ns) > 0:
            self.id = ns + '::' + classname # class name with package / namespace
        else:
            self.id = classname
        print('[' + classname + '] defined in [' + file + '] \'s id = [' + self.id + ']')
        self.parent = None # class name
        self.interfaces = set() # parent interface of the implemented child class ## class id
        self.implements = set() # implement child class of interface ## class id
        self.lchild = set() # set of class name, who relied on current class ## class id
        self.rchild = set() # set of class name, whom current class is relied on ## class id
        self.childs = set() # set of class name, who is inherited from current class ## class id
        self.name = classname
        self.file = file # file with full path, which will be used to identify class' namespace ## nullable
        self.namespace = ns # packagename for java; namespace for c++
        self.displayname = self.name.replace('.', '・').replace('<', '‹').replace('>', '›').replace('/', '_').replace(':','∶')
        self.displayid = self.id.replace('.', '・').replace('<', '‹').replace('>', '›').replace('/', '_').replace(':','∶')
        self.displayns = self.namespace.replace('.', '・').replace('<', '‹').replace('>', '›').replace('/', '_').replace(':','∶')
        ### disable namespace for cpp
        if not file.endswith(r'.java'):
            self.displayid = self.displayname
            self.displayns = ''
        # fixme, we cannot decide rely class whether is under ns or under which ns 
        # if len(ns) > 1:
        #     ns = ns.replace(r'::', '_')
        #     self.displayname = ns + '__' + self.displayname
        # if len(ns) > 1:
        #     if file.endswith('.java'):
        #         self.name = ns + '.' + self.name
        #         self.displayname = ns.replace(r'::',r'_').replace('.', '・').replace('<', '‹').replace('>', '›') + '・' + self.displayname
        #     else:
        #         self.name = ns + '::' + self.name
        #         self.displayname = ns.replace(r'::',r'_').replace('.', '・').replace('<', '‹').replace('>', '›') + '__' + self.displayname
        # gClassnameSet.add(self.name)
        # gClassDefinedFileSet.add(self.file)
        # gDic_Classname_File[self.name] = self.file
        # if self.file in gDic_File_ClassnameSet.keys():
        #     gDic_File_ClassnameSet[self.file] = gDic_File_ClassnameSet.get(self.file).add(self.name)
        # else:
        #     sName = set()
        #     sName.add(self.name)
        #     gDic_File_ClassnameSet[self.file] = sName

    def dumpself(self):
        print('-'*20)
        print(self.id)
        print(self.name)
        print(self.namespace)
        print(self.file)
        print(self.parent)
        print(self.childs)
        print(self.displayid)
        print(self.displayname)
        print(self.displayns)
        print('-'*20)

    def is_valid_node(self):
        return True if self.name is not None and len(self.name) > 0 else False

    def is_equal(self, classid):
        return True if classid == self.id else False

    def is_parent(self):
        return True if len(self.childs) > 0 else False

    def is_interface(self):
        return True if len(self.implements) > 0 else False

    def is_leaf(self):
        return True if len(self.childs) < 1 else False

    def add_parent(self, parent_class_id):
        # parent class of current class
        self.parent = parent_class_id

    def add_child(self, child_class_id):
        # sometimes we don't know it's left or right child
        self.childs.add(child_class_id)

    def add_interface(self, parent_interface_id):
        self.interfaces.add(parent_interface_id)
    
    def add_implement(self, child_implement_id):
        self.implements.add(child_implement_id)

    def add_lchild(self, child_class_id):
        # classes relied on current class
        self.lchild.add(child_class_id)

    def add_rchild(self, child_class_id):
        # classes whom current class is relied on
        self.rchild.add(child_class_id)

    def is_standalone(self):
        if len(self.childs) > 0 \
                or len(self.lchild) > 0 \
                or len(self.rchild) > 0 \
                or len(self.interfaces) > 0 \
                or len(self.implements) > 0 \
                or self.parent is not None:
            return False
        else:
            return True

    def get_id(self):
        return self.id

    def get_classname(self):
        return self.name

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

    def is_parent_of_node(self, clz_id):
        return True if self.parent is not None and self.parent == clz_id else False

    def is_child_of_node(self, clz_id):
        return True if len(self.childs) > 0 and clz_id in self.childs else False

    def is_rely_on_node(self, clz_id):
        return True if len(self.lchild) > 0 and clz_id in self.lchild else False

    def is_relied_by_node(self, clz_id):
        return True if len(self.rchild) > 0 and clz_id in self.rchild else False

    def is_clz_direct_relate_with_node(self, clz_id):
        # only check direct childs and parent
        print_debug('node class ' + self.name + ' , class to check ' + clz_id)
        return True if self.is_parent_of_node(clz_id) \
            or self.is_child_of_node(clz_id) \
            or self.is_rely_on_node(clz_id) \
            or self.is_relied_by_node(clz_id) else False

    def is_clz_relate_with_node_in_depth(self, clz_id, depth, dict_classid_treenode):
        if depth == -1:
            return True
        elif depth == 0:
            return False
        else:
            if self.is_equal(clz_id):
                return True
            elif self.is_parent_of_node(clz_id) or self.is_child_of_node(clz_id):
                return True
            else:
                if len(self.lchild) > 0:
                    for lc in self.lchild:
                        if lc in dict_classid_treenode.keys():
                            nd = dict_classid_treenode.get(lc)
                            if nd.is_clz_relate_with_node_in_depth(clz_id, depth - 1, dict_classid_treenode):
                                return True
                if len(self.rchild) > 0:
                    for rc in self.rchild:
                        if rc in dict_classid_treenode.keys():
                            nd = dict_classid_treenode.get(rc)
                            if nd.is_clz_relate_with_node_in_depth(clz_id, depth - 1, dict_classid_treenode):
                                return True
        return False


def dump(dict_classid_treenode):
    if dict_classid_treenode is not None and len(dict_classid_treenode) > 0:
        for clz in dict_classid_treenode:
            nd = dict_classid_treenode.get(clz)
            print(nd.name)
            if nd.parent is not None:
                print('\t parent = ' + nd.parent)
            else:
                print('\t parent = none')
            print('\t childs = ' + str(nd.childs))
            print('\t relied by ' + str(nd.lchild))
            print('\t relied on ' + str(nd.rchild))


