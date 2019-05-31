# -*- coding: utf-8 -*-

import os
import sys
import re

from tree import TreeNode, dump

KEYWORD_PUBLIC = r"public"
KEYWORD_ABSTRACT = r"(abstract\ +)?"
KEYWORD_CLASS = r"class"
PATTERN_CLASS_NAME = r"[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?"
KEYWORD_EXTEND = r'extends'

SPLIT_SPACE = r'\ +'
SPLIT_SPACE_RETURN = r'(\ +|\n\ *)'
SPLIT_POST = r'(\ |{)'

# public\ +(abstract\ +)?class\ +[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?(\ +|\n\ *)extends(\ +|\n\ *)[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?(\ |{)
PATTERN_CLASS_WITH_PARENT = KEYWORD_PUBLIC + SPLIT_SPACE + \
                            KEYWORD_ABSTRACT + \
                            KEYWORD_CLASS + SPLIT_SPACE + \
                            PATTERN_CLASS_NAME + SPLIT_SPACE_RETURN + \
                            KEYWORD_EXTEND + SPLIT_SPACE_RETURN + \
                            PATTERN_CLASS_NAME + SPLIT_POST

PATTERN_CLASS_DEFINE = KEYWORD_PUBLIC + SPLIT_SPACE + \
                       KEYWORD_ABSTRACT + \
                       KEYWORD_CLASS + SPLIT_SPACE + \
                       PATTERN_CLASS_NAME + SPLIT_SPACE_RETURN


def __init__():
    pass


def draw_class_relationship(dict_class_parent, dict_class_reliedclass, dict_classname_treenode, key_class):
    if dict_classname_treenode is not None and len(dict_classname_treenode) >0:
        fo = open('output', 'w')
        #fo.write('```graphviz')
        fo.write('\ndigraph G {')
        #fo.write('\nrankdir = LR')

        haskey = True if key_class is not None and key_class in dict_classname_treenode.keys() else False
        key_nd = dict_classname_treenode.get(key_class)

        for cls in dict_classname_treenode:
            nd = dict_classname_treenode.get(cls)
            if nd is not None and nd.is_valid_node():
                if nd.is_standalone():
                    print('drop standalone ' + nd.name)
                elif nd.is_equal(key_class):
                    fo.write('\n    ' + nd.displayname + '[shape = egg color=green]')
                elif nd.is_parent():
                    print('parent node ' + nd.name)
                    fo.write('\n    ' + nd.displayname + '[shape = component]')
                elif nd.is_leaf():
                    fo.write('\n    ' + nd.displayname + '[shape = plaintext]')
                else:
                    fo.write('\n    ' + nd.displayname + '[shape = note]')
        if dict_class_parent is not None and len(dict_class_parent) > 0:
            for cls in dict_class_parent:
                if cls is not None and dict_class_parent[cls] is not None:
                    cls_converted = dict_classname_treenode.get(cls).displayname
                    pnt_converted = dict_classname_treenode.get(dict_class_parent[cls]).displayname
                    fo.write('\n    ' + cls_converted + ' -> ' + pnt_converted + '[arrowhead = empty color=purple]')
        if dict_class_reliedclass is not None and len(dict_class_reliedclass) > 0:
            for cls in dict_class_reliedclass:
                if cls is not None:
                    cls_converted = dict_classname_treenode.get(cls).displayname
                    if dict_class_reliedclass is not None:
                        for relatedcls in dict_class_reliedclass.get(cls):
                            if relatedcls != cls:
                                relatedcls_converted = dict_classname_treenode.get(relatedcls).displayname
                                if haskey and \
                                        (key_nd.is_clz_direct_relate_with_node(cls) or
                                         key_nd.is_clz_direct_relate_with_node(relatedcls)):
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
                                elif haskey:
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed color = gray]')
                                else:
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
        fo.write('\n}')
        #fo.write('\n```')
        fo.close()


def scan_class_define(root_dir, mode, excluded_class, key_class):
    dict_filename_classname = {}
    dict_class_parent = {}
    list_class_def = []
    dict_class_reliedclass = {}
    set_class_not_standalone = set()

    dict_classname_treenode = {}
    for root, subdirs, files in os.walk(root_dir):
        print(files)
        for filename in files:
            if filename.find('.java') > 0:
                filepath = os.path.join(root, filename)
                f = open(filepath, 'r')
                classname = ''
                for line in f:
                    if line.startswith('import'):
                        pass
                    elif re.match(PATTERN_CLASS_WITH_PARENT, line):
                        try:
                            classname = re.search(KEYWORD_CLASS + '(.*)' + KEYWORD_EXTEND, line).group(1).strip()
                            parentname = re.search(KEYWORD_EXTEND + '(.*)', line).group(1).lstrip()
                            try:
                                parentname = parentname[:parentname.index(r' ')]
                            except:
                                pass
                            try:
                                parentname = parentname[:parentname.index(r'{')]
                            except:
                                pass
                            should_link = True
                            if len(classname) > 0 and classname not in excluded_class:
                                dict_filename_classname[filename] = classname
                                if classname not in dict_classname_treenode.keys():
                                    nd = TreeNode(classname)
                                    dict_classname_treenode[classname] = nd
                            else:
                                should_link = False
                            if len(parentname) > 0 and parentname not in excluded_class:
                                if parentname not in dict_classname_treenode.keys():
                                    nd = TreeNode(parentname)
                                    dict_classname_treenode[parentname] = nd
                            else:
                                should_link = False
                            if should_link and mode.find('c'):
                                dict_class_parent[classname] = parentname
                                set_class_not_standalone.add(classname)
                                set_class_not_standalone.add(parentname)

                                dict_classname_treenode.get(classname).add_parent(parentname)
                                dict_classname_treenode.get(parentname).add_child(classname)

                        except Exception as e:
                            print('PATTERN_CLASS_WITH_PARENT except\n\t' + str(e))
                        break
                    elif re.match(PATTERN_CLASS_DEFINE, line):
                        classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                        try:
                            classname = classname[:classname.index(r' ')]
                        except Exception as e:
                            print('PATTERN_CLASS_DEFINE except\n\t' + str(e))
                        if len(classname) > 0 and classname not in excluded_class:
                            list_class_def.append(classname)
                            dict_filename_classname[filename] = classname
                            if classname not in dict_classname_treenode.keys():
                                nd = TreeNode(classname)
                                dict_classname_treenode[classname] = nd
                        break
                f.close()
    print('='*20)
    for filename in dict_filename_classname:
        print(filename + ' : ' + dict_filename_classname[filename])
    print('=' * 20)
    if len(dict_classname_treenode) > 0 and mode.find('r') >= 0:
        for root, subdirs, files in os.walk(root_dir):
            print(files)
            for filename in files:
                if filename.find('.java') > 0:
                    filepath = os.path.join(root, filename)
                    print('parsing '+ filename + ' : ' + filepath)
                    f = open(filepath, 'r')
                    buff = f.read()
                    f.close()
                    set_reliedclass = set()

                    fclass = dict_filename_classname.get(filename)

                    if fclass is None:
                        print('should not happen ' + filename)
                        continue

                    if fclass not in dict_classname_treenode:
                        nd = TreeNode(fclass)
                        dict_classname_treenode[fclass] = nd
                    nd_fclass = dict_classname_treenode.get(fclass)

                    for clz in dict_classname_treenode:
                        pat = r"\ " + clz + r"\.|new\ " + clz + r"|\"[a-zA-Z\.]+" + clz + r"\""
                        #print(pat)
                        # \ Intent\.|new Intent
                        if re.search(pat, buff):
                            set_reliedclass.add(clz)
                            set_class_not_standalone.add(clz)
                            # clz's node has created already
                            nd_clz = dict_classname_treenode.get(clz)
                            print('\t find relied class ' + nd_clz.name)
                            nd_clz.add_lchild(fclass)
                            nd_fclass.add_rchild(clz)
                    dict_class_reliedclass[fclass] = set_reliedclass
                    if len(set_reliedclass) < 1:
                        print('\t no relied class')

                    if len(set_reliedclass) > 0:
                        set_class_not_standalone.add(fclass)

    #print(dict_class_reliedclass)
    draw_class_relationship(dict_class_parent, dict_class_reliedclass, dict_classname_treenode, key_class)


def main(root_dir, mode, excluded_class, key_class):
    scan_class_define(root_dir, mode, excluded_class, key_class)


if __name__ == '__main__':
    root_dir = None
    mode = 'ci' # class inherit + interface implement
                # possible value : mix of below values
                #   - 'c' : class
                #   - 'i' : interface
                #   - 'r' : rely
    excluded_class = []
    key_class = None
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            argv = sys.argv[i].strip()
            if argv == '-p':
                try:
                    root_dir = sys.argv[i + 1]
                except:
                    break
            elif argv == '-m':
                try:
                    mode = sys.argv[i + 1]
                except:
                    pass
            elif argv == '-e': # exclued class, split with ','
                try:
                    excluded_class = sys.argv[i + 1].split(',')
                    print(excluded_class)
                except:
                    pass
            elif argv == '-k': # key class wanted to observe
                try:
                    key_class = sys.argv[i + 1]
                except:
                    pass

    else:
        # test only
        #main('/Users/lego/workspace/omadm') # scanning in current directory
        root_dir = '/Users/lego/workspace/OTAProvisioningClient'
        #main('/Users/lego/aosp/packages/apps/Settings/src')

    if root_dir is not None:
        main(root_dir, mode, excluded_class, key_class)
    else:
        print('pls assign root dir to scan with -p')
    exit(0)
