# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess

from tree import TreeNode, dump, print_debug

KEYWORD_PUBLIC = r"public"
KEYWORD_ABSTRACT = r"(abstract\ +)?"
KEYWORD_CLASS = r"class"
PATTERN_CLASS_NAME = r"[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?"
KEYWORD_EXTEND = r'extends'
KEYWORD_EXTEND__CPP = r'\ *:\ *' # with optional split
KEYWORD_BASE_CLASS_OPTIONAL_PREFIX = r'(\ *public\ *|\ *protected\ *|\ *private\ *)?'

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

# class\ +[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?\ *:\ *(\ *public\ *|\ *protected\ *|\ *private\ *)?[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?(\ *,\ *(\ *public\ *|\ *protected\ *|\ *private\ *)?[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?)*\ *\n*\ *{
# change from r'\ *\n*\ *{' to r'\ *(\n|{)', as we scan line by line
PATTERN_CLASS_WITH_PARENT__CPP = KEYWORD_CLASS + SPLIT_SPACE + \
                                 PATTERN_CLASS_NAME + KEYWORD_EXTEND__CPP + \
                                 KEYWORD_BASE_CLASS_OPTIONAL_PREFIX + PATTERN_CLASS_NAME + \
                                 r'(' + r'\ *,\ *' + KEYWORD_BASE_CLASS_OPTIONAL_PREFIX + PATTERN_CLASS_NAME + r')*' + \
                                 r'\ *(\n|{)'

# class\ +[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?\ *\n*\ *{
PATTERN_CLASS_DEFINE__CPP = KEYWORD_CLASS + SPLIT_SPACE + \
                            PATTERN_CLASS_NAME + r'\ *\n*\ *{'

CLASS_EXCLUDED_ALWAYS = [
    r'ByteArray',
]

CACHED_INFO = []


def __init__():
    pass


def do_real_draw_if_possible(input, type):
    try:
        dot_v = subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;dot -V')
        fdp_v = subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;fdp -V')
        dot_support = True if dot_v[0] == 0 and dot_v[1].find('graphviz') > 0 else False
        fdp_support = True if fdp_v[0] == 0 and fdp_v[1].find('graphviz') > 0 else False

        if dot_support or fdp_support:
            print('\ntry to draw png with local installed graphviz')
        outpath = os.path.join(os.path.expanduser("~"), 'Downloads')

        if dot_support:
            subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;dot ' + input + ' -Gdpi=300 -T png -o ' + os.path.join(outpath, type + 'graph-dot.png'))
            print('dot png: ' + outpath + '/graph-dot.png')
        if fdp_support:
            subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;fdp ' + input + ' -Gdpi=300 -T png -o ' + os.path.join(outpath, type + 'graph-fdp.png'))
            print('fdp png: ' + outpath + '/graph-fdp.png')
    except Exception as e:
        print('do_real_draw_if_possible get ' + str(e))


def draw_class_relationship(root_dir, dict_class_parent, dict_class_reliedclass, dict_classname_treenode, key_class, depth, type):
    if dict_classname_treenode is not None and len(dict_classname_treenode) >0:
        set_class_depth_exceeded = set()

        fo = open(os.path.join(root_dir, type + 'output'), 'w')
        fo.write('# ' + ' '.join(sys.argv))
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
                elif haskey and not key_nd.is_clz_relate_with_node_in_depth(cls, depth, dict_classname_treenode):
                    set_class_depth_exceeded.add(cls)
                    CACHED_INFO.append('drop depth exceeded ' + cls)
                elif nd.is_parent():
                    print('parent node ' + nd.name)
                    fo.write('\n    ' + nd.displayname + '[shape = component]')
                elif nd.is_leaf():
                    fo.write('\n    ' + nd.displayname + '[shape = plaintext]')
                else:
                    fo.write('\n    ' + nd.displayname + '[shape = note]')
        if len(set_class_depth_exceeded) > 0:
            for c in set_class_depth_exceeded:
                nc = dict_classname_treenode.get(c)
                if nc.parent is not None:
                    dict_classname_treenode.get(nc.parent).childs.remove(c)
                for ic in nc.childs:
                    dict_classname_treenode.get(ic).parent = None
                for lc in nc.lchild:
                    dict_classname_treenode.get(lc).rchild.remove(c)
                for rc in nc.rchild:
                    dict_classname_treenode.get(rc).lchild.remove(c)
                del dict_classname_treenode[c]
        if dict_class_parent is not None and len(dict_class_parent) > 0:
            for cls in dict_class_parent:
                if cls not in dict_classname_treenode.keys() or \
                   dict_class_parent[cls] not in dict_classname_treenode.keys():
                    CACHED_INFO.append('skip ' + cls + ' --▷ ' + dict_class_parent[cls])
                    continue
                if cls is not None and dict_class_parent[cls] is not None:
                    cls_converted = dict_classname_treenode.get(cls).displayname
                    pnt_converted = dict_classname_treenode.get(dict_class_parent[cls]).displayname
                    fo.write('\n    ' + cls_converted + ' -> ' + pnt_converted + '[arrowhead = empty color=purple]')
        if dict_class_reliedclass is not None and len(dict_class_reliedclass) > 0:
            for cls in dict_class_reliedclass:
                if cls is not None and cls in dict_classname_treenode:
                    cls_converted = dict_classname_treenode.get(cls).displayname
                    if dict_class_reliedclass is not None:
                        for relatedcls in dict_class_reliedclass.get(cls):
                            if relatedcls not in dict_classname_treenode:
                                CACHED_INFO.append('skip ' + cls + ' --> ' + relatedcls)
                                continue
                            if relatedcls != cls:
                                relatedcls_converted = dict_classname_treenode.get(relatedcls).displayname
                                if haskey and \
                                        (key_nd.is_equal(cls) or
                                         key_nd.is_equal(relatedcls)):
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
                                elif haskey:
                                    if cls not in set_class_depth_exceeded and \
                                       relatedcls not in set_class_depth_exceeded:
                                        fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed color = gray]')
                                    else:
                                        CACHED_INFO.append('drop relationship ' + cls + ' --> ' + relatedcls + ' due to depth exceed')
                                else:
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
                else:
                    CACHED_INFO.append('skip ' + cls + ' --> ...')
        fo.write('\n}')
        #fo.write('\n```')
        fo.close()
    for ln in CACHED_INFO:
        print(ln)
    print('\noutput: ' + root_dir + '/' + type + 'output')
    do_real_draw_if_possible(os.path.join(root_dir, type + 'output'), type)


def scan_class_define(root_dir, mode, excluded_class, key_class, depth):
    dict_filename_classname = {}
    dict_class_parent = {}
    list_class_def = []
    dict_class_reliedclass = {}

    dict_filename_classname__cpp = {}
    dict_class_parent__cpp = {}
    list_class_def__cpp = []
    dict_class_reliedclass__cpp = {}

    dict_classname_treenode = {}
    dict_classname_treenode__cpp = {}
    for root, subdirs, files in os.walk(root_dir):
        print(files)
        for filename in files:
            print(' scanning 1 stage : ' + filename)
            if filename.find('.java') > 0:
                filepath = os.path.join(root, filename)
                f = open(filepath, 'r')
                classname = ''
                for line in f:
                    if line.startswith('import') or line.startswith(r'/') or line.startswith(r'*'):
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
                            if mode.find('c') >= 0 and len(parentname) > 0 and parentname not in excluded_class:
                                if parentname not in dict_classname_treenode.keys():
                                    nd = TreeNode(parentname)
                                    dict_classname_treenode[parentname] = nd
                            else:
                                should_link = False
                            if should_link:
                                dict_class_parent[classname] = parentname

                                dict_classname_treenode.get(classname).add_parent(parentname)
                                dict_classname_treenode.get(parentname).add_child(classname)
                            else:
                                CACHED_INFO.append('drop inherit relationship ' + classname + ' --▷ ' + parentname)

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
            elif filename.endswith('.h') > 0:
                filepath = os.path.join(root, filename)
                f = open(filepath, 'r')
                classname = ''
                for line in f:
                    line = line.lstrip()
                    if line.startswith('#') or line.startswith(r'/') or line.startswith(r'*'):
                        pass
                    elif re.match(PATTERN_CLASS_WITH_PARENT__CPP, line):
                        try:
                            classname = re.search(KEYWORD_CLASS + '(.*)' + KEYWORD_EXTEND__CPP, line).group(1).strip()
                            parentname_multi = re.search(KEYWORD_EXTEND__CPP + '(.*)', line).group(1).lstrip()
                            try:
                                parentname_multi = parentname_multi[:parentname_multi.index(r'\n')]
                            except:
                                pass
                            try:
                                parentname_multi = parentname_multi[:parentname_multi.index(r'{')]
                            except:
                                pass
                            try:
                                parentname_multi = parentname_multi.replace(r'public ', r'')
                            except:
                                pass
                            try:
                                parentname_multi = parentname_multi.replace(r'protected ', r'')
                            except:
                                pass
                            try:
                                parentname_multi = parentname_multi.replace(r'private ', r'')
                            except:
                                pass
                            should_link = True
                            if len(classname) > 0 and classname not in excluded_class:
                                dict_filename_classname__cpp[filename] = classname
                                if classname not in dict_classname_treenode__cpp.keys():
                                    nd = TreeNode(classname)
                                    dict_classname_treenode__cpp[classname] = nd
                            else:
                                should_link = False
                            if should_link:
                                parentnames = parentname_multi.split(',')
                                for parentname in parentnames:
                                    parentname = parentname.strip()
                                    if mode.find('c') >= 0 and len(parentname) > 0 and parentname not in excluded_class:
                                        if parentname not in dict_classname_treenode__cpp.keys():
                                            nd = TreeNode(parentname)
                                            dict_classname_treenode__cpp[parentname] = nd
                                    else:
                                        should_link = False
                                    if should_link:
                                        dict_class_parent__cpp[classname] = parentname

                                        dict_classname_treenode__cpp.get(classname).add_parent(parentname)
                                        dict_classname_treenode__cpp.get(parentname).add_child(classname)
                                    else:
                                        CACHED_INFO.append('drop inherit relationship [cpp] ' + classname + ' --▷ ' + parentname)
                            else:
                                CACHED_INFO.append('drop inherit relationship [cpp] ' + classname + ' --▷ ' + parentname_multi)

                        except Exception as e:
                            print('PATTERN_CLASS_WITH_PARENT__CPP except\n\t' + str(e))
                        break
                    elif re.match(PATTERN_CLASS_DEFINE__CPP, line):
                        classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                        try:
                            classname = classname[:classname.index(r' ')]
                        except Exception as e:
                            print('PATTERN_CLASS_DEFINE__CPP except\n\t' + str(e))
                        if len(classname) > 0 and classname not in excluded_class:
                            list_class_def__cpp.append(classname)
                            dict_filename_classname__cpp[filename] = classname
                            if classname not in dict_classname_treenode__cpp.keys():
                                nd = TreeNode(classname)
                                dict_classname_treenode__cpp[classname] = nd
                        break
                f.close()
    print('='*20)
    for filename in dict_filename_classname:
        print(filename + ' : ' + dict_filename_classname[filename])
    print('-'*8 + 'c++' + '-'*8)
    for filename in dict_filename_classname__cpp:
        print(filename + ' : ' + dict_filename_classname__cpp[filename])
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
                        pat = r"\ " + clz + r"\.|new\ " + clz + r"|\"[a-zA-Z]+\." + clz + r"\""
                        #print(pat)
                        # \ Intent\.|new Intent
                        if re.search(pat, buff):
                            set_reliedclass.add(clz)
                            # clz's node has created already
                            nd_clz = dict_classname_treenode.get(clz)
                            print('\t find relied class ' + nd_clz.name)
                            nd_clz.add_lchild(fclass)
                            nd_fclass.add_rchild(clz)
                    dict_class_reliedclass[fclass] = set_reliedclass
                    if len(set_reliedclass) < 1:
                        print('\t no relied class')
                elif filename.endswith('.h'):
                    filepath = os.path.join(root, filename)
                    print('parsing '+ filename + ' : ' + filepath)
                    f = open(filepath, 'r')
                    buff = f.read()
                    f.close()
                    set_reliedclass = set()

                    fclass = dict_filename_classname__cpp.get(filename)

                    if fclass is None:
                        print('should not happen ' + filename)
                        continue

                    if fclass not in dict_classname_treenode__cpp:
                        nd = TreeNode(fclass)
                        dict_classname_treenode__cpp[fclass] = nd
                    nd_fclass = dict_classname_treenode__cpp.get(fclass)

                    for clz in dict_classname_treenode__cpp:
                        pat = r'\ *' + clz + r'(<\w+>)?' + r'\ *' + r'\*?' + r'\ *' + r'\w+' + r'\ *\w+\ *;'
                        # \ Intent\.|new Intent
                        if re.search(pat, buff):
                            set_reliedclass.add(clz)
                            # clz's node has created already
                            nd_clz = dict_classname_treenode__cpp.get(clz)
                            print('\t find relied class ' + nd_clz.name)
                            nd_clz.add_lchild(fclass)
                            nd_fclass.add_rchild(clz)
                    dict_class_reliedclass__cpp[fclass] = set_reliedclass
                    if len(set_reliedclass) < 1:
                        print('\t no relied class')

    #print(dict_class_reliedclass)
    if len(dict_classname_treenode) > 0:
        draw_class_relationship(root_dir, dict_class_parent, dict_class_reliedclass, dict_classname_treenode, key_class, depth, "java")
    if len(dict_classname_treenode__cpp) > 0:
        draw_class_relationship(root_dir, dict_class_parent__cpp, dict_class_reliedclass__cpp, dict_classname_treenode__cpp, key_class, depth, "cpp")


def main(root_dir, mode, excluded_class, key_class, depth):
    scan_class_define(root_dir, mode, excluded_class, key_class, depth)


def print_help():
    print('''
Usage: python scan_clazz.py -p dir_to_scan [options]

    Options:
    -m mode
            mode can be 'c' 'i' 'r', or combine
            'c' - parsing class and inherit
            'i' - parsing interface and implement (NOT supported)
            'r' - parsing relationship between classes (used by)
    -e class[,class2,class3,...,classn]
            exclude classes in parsing result
    -k class
            assign the key class which will be emphasized in output
    -d depth
            take effect only if key class is assigned
            valid depth must be a integer between [3-9], include 3 and 9
            otherwise depth will be discarded
            depth is calculated from key class, a class direct rely on / relied by key class has depth 1 
    ''')


if __name__ == '__main__':
    CACHED_INFO.append('\nscan cmd\n\t' + ' '.join(sys.argv))

    root_dir = None
    mode = 'ci'  # class inherit + interface implement
                 # possible value : mix of below values
                 #   - 'c' : class
                 #   - 'i' : interface
                 #   - 'r' : rely
    excluded_class = []
    key_class = None
    depth = -1  # unlimited, valid depth is [3-9], other value will be ignored
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            argv = sys.argv[i].strip()
            if argv == '-h':
                print_help()
                os._exit(0)
            elif argv == '-p':
                try:
                    root_dir = sys.argv[i + 1]
                except:
                    break
            elif argv == '-m':
                try:
                    mode = sys.argv[i + 1]
                except:
                    pass
            elif argv == '-e':  # excluded class, split with ','
                try:
                    excluded_class = sys.argv[i + 1].split(',')
                    print('user passed excluded class list : ' + str(excluded_class))
                except:
                    pass
            elif argv == '-k':  # key class wanted to observe
                try:
                    key_class = sys.argv[i + 1]
                except:
                    pass
            elif argv == '-d':  # max depth from key class, will be dropped if key class is not assigned
                try:
                    depth = int(sys.argv[i + 1])
                    if depth < 3 or depth > 9:
                        depth = -1
                        CACHED_INFO.append('depth ' + str(depth) + ' is dropped as it\'s not in [3-9]')
                except:
                    pass

    else:
        # test only
        #main('/Users/lego/workspace/omadm') # scanning in current directory
        #root_dir = '/Users/lego/workspace/OTAProvisioningClient'
        #main('/Users/lego/aosp/packages/apps/Settings/src')
        print_help()
        os._exit(0)

    if key_class is None and (2 < depth < 10):
        depth = -1
        CACHED_INFO.append('depth ' + str(depth) + ' is dropped as key class is not assigned')

    if root_dir is not None:
        excluded_class = CLASS_EXCLUDED_ALWAYS + excluded_class
        print('final excluded class list : ' + str(excluded_class))
        main(root_dir, mode, excluded_class, key_class, depth)
    else:
        print('pls assign root dir to scan with -p')
    os._exit(0)
