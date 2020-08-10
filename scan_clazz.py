# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess

from tree import TreeNode, dump, print_debug, debug
from clz import ClzRelationShips
from util_namespace import NameSpaceUtil

KEYWORD_PUBLIC = r"public"
KEYWORD_ABSTRACT = r"(final\ +)?(abstract\ +)?(final\ +)?"
KEYWORD_CLASS = r"class"
PATTERN_CLASS_NAME = r"[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?"
KEYWORD_EXTEND = r'extends'
KEYWORD_EXTEND__CPP = r'\ *\:\ *' # with optional split
KEYWORD_BASE_CLASS_OPTIONAL_PREFIX = r'(\ *public\ *|\ *protected\ *|\ *private\ *)?(\ *virtual\ *)?'

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

PATTERN_CLASS_IMPLEMENT_INTERFACE = r'public\ *(final)?\ *class [0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)? \w*\ *[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)? implements ([0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?(,)?\ *)+\ *({|,|\n)'
#r'public class [0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)? \w*\ *[0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)? implements ([0-9a-zA-Z_\.]*(<[0-9a-zA-Z_\.]*>)?(,)?\ *)+\ *{'

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
    r'Activity',
    r'Thread',
    r'Application',
    r'Item',
    r'BaseActivity',
    r'ListView',
    r'Fragment',
    r'Dialog',
    r'DialogFragment',
    r'Service',
    r'BroadcastReceiver',
    r'TextView',
    r'LinearLayout',
    r'Exception',
    r'Executor',
    r'AbstractCursor',
    r'State',
    r'*Test',
    r'Preference',
    r'PreferenceGroup',
    r'CheckBoxPreference',
]

CACHED_INFO = []


def __init__():
    pass


def do_real_draw_if_possible(input, lang):
    try:
        dot_v = subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;dot -V')
        fdp_v = subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;fdp -V')
        dot_support = True if dot_v[0] == 0 and dot_v[1].find('graphviz') > 0 else False
        fdp_support = True if fdp_v[0] == 0 and fdp_v[1].find('graphviz') > 0 else False

        if dot_support or fdp_support:
            print('\ntry to draw png with local installed graphviz')
        outpath = os.path.join(os.path.expanduser("~"), 'Downloads')

        if dot_support:
            subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;dot ' + input + ' -Gdpi=300 -T png -o ' + os.path.join(outpath, lang + 'graph-dot.png'))
            print('dot png: ' + outpath + '/graph-dot.png')
        if fdp_support:
            subprocess.getstatusoutput(r'export PATH=/usr/local/bin:$PATH;fdp ' + input + ' -Gdpi=300 -T png -o ' + os.path.join(outpath, lang + 'graph-fdp.png'))
            print('fdp png: ' + outpath + '/graph-fdp.png')
    except Exception as e:
        print('do_real_draw_if_possible get ' + str(e))
    print('\n\n')


def draw_class_relationship(mClzRelationShips):
    root_dir = mClzRelationShips.get_var("root_dir")
    dict_classid_parentid = mClzRelationShips.get_var("dict_classid_parentid")
    dict_classid_interfaceid = mClzRelationShips.get_var("dict_classid_interfaceid")
    dict_classid_reliedclass = mClzRelationShips.get_var("dict_classid_reliedclass")
    dict_classid_treenode = mClzRelationShips.get_var("dict_classid_treenode")
    set_classname = mClzRelationShips.get_var("set_classname")
    key_class = mClzRelationShips.get_var("key_class")
    key_class_id = mClzRelationShips.get_var("key_class_id")
    depth = mClzRelationShips.get_var("depth")
    lang = mClzRelationShips.get_var("lang")
    if dict_classid_treenode is not None and len(dict_classid_treenode) >0:
        set_class_depth_exceeded = set()

        fo = open(os.path.join(root_dir, lang + 'output'), 'w')
        fo.write('# ' + ' '.join(sys.argv))
        #fo.write('```graphviz')
        fo.write('\ndigraph G {')
        #fo.write('\nrankdir = LR')

        haskey = True if key_class is not None and key_class in set_classname and key_class_id in dict_classid_treenode else False
        key_nd = dict_classid_treenode.get(key_class_id)
        print('key_nd = ' + str(key_nd))

        for cls_id in dict_classid_treenode:
            nd = dict_classid_treenode.get(cls_id)
            if nd is not None and nd.is_valid_node():
                if nd.is_standalone():
                    print('drop standalone ' + nd.id)
                elif nd.is_equal(key_class_id):
                    fo.write('\n    ' + nd.displayid + '[shape = egg color=green]')
                elif haskey and not key_nd.is_clz_relate_with_node_in_depth(cls_id, depth, dict_classid_treenode):
                    set_class_depth_exceeded.add(cls_id)
                    CACHED_INFO.append('drop depth exceeded ' + nd.id)
                elif nd.is_parent():
                    print('parent node ' + nd.name)
                    fo.write('\n    ' + nd.displayid + '[shape = plaintext label="' + nd.displayname + r'\n[' + nd.displayns + ']"]')#'[shape = component]')
                elif nd.is_interface():
                    print('interface node ' + nd.name)
                    fo.write('\n    ' + nd.displayid + '[shape = plaintext label="' + nd.displayname + r'\n[' + nd.displayns + ']"]')#'[shape = component]')
                elif nd.is_leaf():
                    fo.write('\n    ' + nd.displayid + '[shape = plaintext label="' + nd.displayname + r'\n[' + nd.displayns + ']"]')
                else:
                    fo.write('\n    ' + nd.displayid + '[shape = note label="' + nd.displayname + r'\n[' + nd.displayns + ']"]')
            else:
                print('invalid node found')
        if len(set_class_depth_exceeded) > 0:
            for c in set_class_depth_exceeded:
                nc = dict_classid_treenode.get(c)
                if nc.parent is not None:
                    dict_classid_treenode.get(nc.parent).childs.remove(c)
                for ic in nc.childs:
                    dict_classid_treenode.get(ic).parent = None
                for lc in nc.lchild:
                    dict_classid_treenode.get(lc).rchild.remove(c)
                for rc in nc.rchild:
                    dict_classid_treenode.get(rc).lchild.remove(c)
                del dict_classid_treenode[c]
        if dict_classid_parentid is not None and len(dict_classid_parentid) > 0:
            for cls_id in dict_classid_parentid:
                if cls_id not in dict_classid_treenode.keys() or \
                   dict_classid_parentid[cls_id] not in dict_classid_treenode.keys():
                    CACHED_INFO.append('skip inherit "' + cls_id + '" --▷ "' + dict_classid_parentid[cls_id] + '"')
                    continue
                if cls_id is not None and dict_classid_parentid[cls_id] is not None:
                    cls_converted = dict_classid_treenode.get(cls_id).displayid
                    pnt_converted = dict_classid_treenode.get(dict_classid_parentid[cls_id]).displayid
                    fo.write('\n    ' + cls_converted + ' -> ' + pnt_converted + '[arrowhead = empty color=purple]')
        if dict_classid_interfaceid is not None and len(dict_classid_interfaceid) > 0:
            for cls_id in dict_classid_interfaceid:
                if cls_id not in dict_classid_treenode.keys() or \
                   dict_classid_interfaceid[cls_id] not in dict_classid_treenode.keys():
                    CACHED_INFO.append('skip interface "' + cls_id + '" - -▷ "' + dict_classid_interfaceid[cls_id] + '"')
                    continue
                if cls_id is not None and dict_classid_interfaceid[cls_id] is not None:
                    cls_converted = dict_classid_treenode.get(cls_id).displayid
                    pnt_converted = dict_classid_treenode.get(dict_classid_interfaceid[cls_id]).displayid
                    fo.write('\n    ' + cls_converted + ' -> ' + pnt_converted + '[arrowhead = empty color=purple style=dashed]')
        if dict_classid_reliedclass is not None and len(dict_classid_reliedclass) > 0:
            for cls_id in dict_classid_reliedclass:
                if cls_id is not None and cls_id in dict_classid_treenode:
                    cls_converted = dict_classid_treenode.get(cls_id).displayid
                    if dict_classid_reliedclass is not None:
                        for relatedcls in dict_classid_reliedclass.get(cls_id):
                            print('checking ' + cls_id + ' \'s relatedcls = ' + str(relatedcls))
                            if relatedcls not in dict_classid_treenode:
                                print('skipping ' + cls_id + ' \'s relatedcls = ' + str(relatedcls))
                                CACHED_INFO.append('skip ' + cls_id + ' --> ' + relatedcls)
                                continue
                            if relatedcls != cls_id:
                                relatedcls_converted = dict_classid_treenode.get(relatedcls).displayid
                                if haskey and \
                                        (key_nd.is_equal(cls_id) or
                                         key_nd.is_equal(relatedcls)):
                                    print('writting 1 ' + cls_id + ' -> ' + str(relatedcls) + '\t: ' + cls_converted + ' -> ' + relatedcls_converted)
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
                                elif haskey:
                                    if cls_id not in set_class_depth_exceeded and \
                                       relatedcls not in set_class_depth_exceeded:
                                        print('writting 2 ' + cls_id + ' -> ' + str(relatedcls) + '\t: ' + cls_converted + ' -> ' + relatedcls_converted)
                                        fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed color = gray]')
                                    else:
                                        CACHED_INFO.append('drop relationship ' + cls_id + ' --> ' + relatedcls + ' due to depth exceed')
                                else:
                                    print('writting 3 ' + cls_id + ' -> ' + str(relatedcls) + '\t: ' + cls_converted + ' -> ' + relatedcls_converted)
                                    fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
                else:
                    CACHED_INFO.append('skip ' + cls_id + ' --> ...')
        fo.write('\n}')
        #fo.write('\n```')
        fo.close()
    for ln in CACHED_INFO:
        print(ln)
    print('\noutput: ' + root_dir + '/' + lang + 'output')
    do_real_draw_if_possible(os.path.join(root_dir, lang + 'output'), lang)

def fliter_clz(clz, ex_clz_list):
    return True if clz not in ex_clz_list and not clz.endswith('Test') else False

# return package and classname with package
def getBestPackageName(clz, pkgSet, curPkg):
    pkgname = curPkg + r'.' +clz # suppose in same package
    if pkgSet is not None and len(pkgSet) > 0:
        for pkg in pkgSet:
            if pkg.endswith(r'.' + clz):
                pkgname = pkg
                break  # current we match 1st one, but not best one
    print('getBestPackageName [ ' + pkgname + ' ] for clz [ ' + clz + ' ]')
    return [pkgname.replace(r'.' + clz, ''), pkgname]

def guessHeaderFromClassName(clz, includedHeaderSet):
    hdfile = ''
    if includedHeaderSet is not None and len(includedHeaderSet) > 0:
        for hd in includedHeaderSet:
            if hd.endswith(clz + '.h'):
                hdfile = hd
                break # current we match 1st one, but not best one
    return hdfile

def scan_class_define(sRootDir, mode, included_java_class, included_cpp_class, excluded_class, key_class, depth):
    dict_filename_classid = {}
    dict_classid_parentid = {}
    dict_classid_interfaceid = {}
    list_classid_def = []
    set_classname = set()
    dict_classid_reliedclass = {}

    dict_filename_classid__cpp = {}
    dict_classid_parentid__cpp = {}
    list_classid_def__cpp = []
    set_classname__cpp = set()
    dict_classid_reliedclassidSet__cpp = {}

    dict_classid_treenode = {}
    dict_classid_treenode__cpp = {}

    dict_classid_filename__cpp = {}

    key_class_id = None

    for jc in included_java_class:
        nd = TreeNode(jc, 'null_file')
        dict_classid_treenode[nd.get_id()] = nd
        set_classname.add(nd.get_classname())
        if jc == key_class:
            key_class_id = nd.get_id()
    for cc in included_cpp_class:
        nd = TreeNode(cc, 'null_file')
        dict_classid_treenode__cpp[nd.get_id()] = nd
        set_classname__cpp.add(nd.get_classname())
        if cc == key_class:
            key_class_id = nd.get_id()

    # 1st scanning, parse all class

    # 2nd scanning, create relationship
    for root_dir in sRootDir:
        for root, subdirs, files in os.walk(root_dir):
            print('file tree \t' + str(files))
            for filename in files:
                print('scanning \t' + filename)
                if filename.find('.java') > 0:
                    filepath = os.path.join(root, filename)
                    f = open(filepath, 'r')
                    currentPkg = ''
                    importedPkgSet = set()
                    for line in f:
                        classname = ''
                        line_classid = ''
                        line_parentid = ''
                        line_interfaceid = ''
                        if line.strip().startswith('package') or \
                        line.strip().startswith('import') or \
                        line.strip().startswith(r'/') or \
                        line.strip().startswith(r'*'):
                            if line.strip().startswith('package'):
                                currentPkg = line.strip().replace(r'package', '').replace(r';','').strip()
                            elif line.strip().startswith('import'):
                                importedPkgSet.add(line.strip().replace(r'import', '').replace(r';','').strip())
                            continue
                        elif re.match(PATTERN_CLASS_WITH_PARENT, line) or re.match(PATTERN_CLASS_IMPLEMENT_INTERFACE, line):
                            if re.match(PATTERN_CLASS_WITH_PARENT, line):
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
                                    parentpkgname = getBestPackageName(parentname, importedPkgSet, currentPkg)
                                    should_link = True
                                    if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                        nd = TreeNode(classname, filepath, currentPkg)
                                        line_classid = nd.get_id()
                                        if line_classid not in dict_classid_treenode.keys():
                                            dict_classid_treenode[line_classid] = nd
                                            set_classname.add(classname)
                                            key_class_id = line_classid if classname == key_class else key_class_id
                                        dict_filename_classid[filename] = line_classid
                                    else:
                                        should_link = False
                                    if mode.find('c') >= 0 and len(parentname) > 0 and fliter_clz(parentname,excluded_class):
                                        nd = TreeNode(parentname, '', parentpkgname[0])
                                        line_parentid = nd.get_id()
                                        if line_parentid not in dict_classid_treenode.keys():
                                            dict_classid_treenode[line_parentid] = nd
                                            set_classname.add(parentname)
                                            key_class_id = line_parentid if parentname == key_class else key_class_id
                                    else:
                                        should_link = False
                                    if should_link:
                                        dict_classid_parentid[line_classid] = line_parentid

                                        dict_classid_treenode.get(line_classid).add_parent(line_parentid)
                                        dict_classid_treenode.get(line_parentid).add_child(line_classid)
                                    else:
                                        CACHED_INFO.append('drop inherit relationship ' + classname + ' --▷ ' + parentname)

                                except Exception as e:
                                    print('PATTERN_CLASS_WITH_PARENT except\n\t' + str(e))
                            if re.match(PATTERN_CLASS_IMPLEMENT_INTERFACE, line):
                                try:
                                    classname = re.search(KEYWORD_CLASS + '(.*)' + r' implements ', line).group(1).strip()
                                    if classname.find(r' extends ') > -1:
                                        classname = classname[:classname.find(r' extends ')]
                                    interfaces = re.search('implements ' + '(.*)', line).group(1).strip()
                                    if interfaces.find(r' extends ') > -1:
                                        interfaces = interfaces[:interfaces.find(r' extends ')]
                                    try:
                                        interfaces = interfaces[:interfaces.index(r'{')]
                                    except:
                                        pass
                                    classname = classname.strip()
                                    should_link = True
                                    if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                        nd = TreeNode(classname, filepath, currentPkg)
                                        line_classid = nd.get_id()
                                        if line_classid not in dict_classid_treenode.keys():
                                            dict_classid_treenode[line_classid] = nd
                                            set_classname.add(classname)
                                            key_class_id = line_classid if classname == key_class else key_class_id
                                        dict_filename_classid[filename] = line_classid
                                    else:
                                        should_link = False
                                    
                                    for interface in interfaces.split(r','):
                                        interface = interface.strip()
                                        interfacepkgname = getBestPackageName(interface, importedPkgSet, currentPkg)
                                        if mode.find('i') >= 0 and fliter_clz(interface,excluded_class):
                                            nd = TreeNode(interface, '', interfacepkgname[0])
                                            line_interfaceid = nd.get_id()
                                            if line_interfaceid not in dict_classid_treenode.keys():
                                                dict_classid_treenode[line_interfaceid] = nd
                                                set_classname.add(interface)
                                                key_class_id = line_interfaceid if interface == key_class else key_class_id
                                        else:
                                            should_link = False
                                        if should_link:
                                            dict_classid_interfaceid[line_classid] = line_interfaceid

                                            dict_classid_treenode.get(line_classid).add_interface(line_interfaceid)
                                            dict_classid_treenode.get(line_interfaceid).add_implement(line_classid)
                                        else:
                                            CACHED_INFO.append('drop interface relationship ' + line_classid + ' --▷ ' + line_interfaceid)
                                except Exception as e:
                                    print('PATTERN_CLASS_IMPLEMENT_INTERFACE except\n\t' + str(e))
                            break
                        elif re.match(PATTERN_CLASS_DEFINE, line):
                            classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                            try:
                                classname = classname[:classname.index(r' ')]
                            except Exception as e:
                                print('PATTERN_CLASS_DEFINE except\n\t' + str(e))
                            if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                nd = TreeNode(classname, filepath, currentPkg)
                                line_classid = nd.get_id()
                                list_classid_def.append(line_classid)
                                dict_filename_classid[filename] = line_classid
                                if line_classid not in dict_classid_treenode.keys():
                                    dict_classid_treenode[line_classid] = nd
                                    set_classname.add(classname)
                                    key_class_id = line_classid if classname == key_class else key_class_id
                            break
                    f.close()
                elif filename.endswith('.h') > 0:
                    filepath = os.path.join(root, filename)
                    f = open(filepath, 'r')
                    includedHeaderSet = set()
                    ns_util = NameSpaceUtil()
                    for line in f:
                        classname = ''
                        line_h_classid = ''
                        line_h_parentid = ''
                        line = line.lstrip()
                        if line.startswith('#') or line.startswith(r'/') or line.startswith(r'*'):
                            if line.strip().startswith('#include '):
                                includedHeaderSet.add(line.strip().replace(r'#include ', '').replace(r'"','').replace(r'<', '').replace(r'>', '').strip())
                            continue
                        ns_util.pushpop(line)
                        print('fsdlkfjldjfsl --- pre begin ' + str(line))
                        if re.match(PATTERN_CLASS_WITH_PARENT__CPP, line):
                            print('fsdlkfjldjfsl --- begin ' + str(line))
                            try:
                                classname = re.search(KEYWORD_CLASS + '(.*)' + KEYWORD_EXTEND__CPP, line).group(1).strip()
                                print('fsdlkfjldjfsl --- begin get class name' + str(classname))
                                parentname_multi = re.search(KEYWORD_EXTEND__CPP + '(.*)', line).group(1).lstrip()
                                print('fsdlkfjldjfsl --- begin get parenetname name' + str(parentname_multi))
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
                                try:
                                    parentname_multi = parentname_multi.replace(r'virtual ', r'')
                                except:
                                    pass
                                should_link = True
                                if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                    ns = ns_util.getNamespace()
                                    nd = TreeNode(classname, filepath, ns)
                                    line_h_classid = nd.get_id()
                                    dict_filename_classid__cpp[filename] = line_h_classid
                                    if line_h_classid not in dict_classid_treenode__cpp.keys():
                                        dict_classid_treenode__cpp[line_h_classid] = nd
                                        set_classname__cpp.add(classname)
                                        key_class_id = line_h_classid if classname == key_class else key_class_id
                                        dict_classid_filename__cpp[line_h_classid] = filename
                                else:
                                    should_link = False
                                if should_link:
                                    parentnames = parentname_multi.split(',')
                                    for parentname in parentnames:
                                        parentname = parentname.strip()
                                        if mode.find('c') >= 0 and len(parentname) > 0 and fliter_clz(parentname,excluded_class):
                                            nd = TreeNode(parentname, guessHeaderFromClassName(parentname, includedHeaderSet))
                                            line_h_parentid = nd.get_id()
                                            if line_h_parentid not in dict_classid_treenode__cpp.keys():
                                                dict_classid_treenode__cpp[line_h_parentid] = nd
                                                set_classname__cpp.add(parentname)
                                                key_class_id = line_h_parentid if parentname == key_class else key_class_id
                                        else:
                                            should_link = False
                                        if should_link:
                                            dict_classid_parentid__cpp[line_h_classid] = line_h_parentid
                                            dict_classid_treenode__cpp.get(line_h_classid).add_parent(line_h_parentid)
                                            dict_classid_treenode__cpp.get(line_h_parentid).add_child(line_h_classid)
                                            print('create inherit relationship [cpp] ' + line_h_classid + ' --▷ ' + line_h_parentid)
                                        else:
                                            CACHED_INFO.append('drop inherit relationship [cpp] ' + line_h_classid + ' --▷ ' + line_h_parentid)
                                else:
                                    CACHED_INFO.append('drop inherit relationship [cpp] ' + classname + ' --▷ ' + parentname_multi)
                                print('fsdlkfjldjfsl --- end ' + str(line))
                            except Exception as e:
                                print('PATTERN_CLASS_WITH_PARENT__CPP [ ' + PATTERN_CLASS_WITH_PARENT__CPP + ' ] except\n\t' + str(e) + '\n\t in ' + line)
                            break
                        elif re.match(PATTERN_CLASS_DEFINE__CPP, line):
                            classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                            try:
                                classname = classname[:classname.index(r' ')]
                            except Exception as e:
                                print('PATTERN_CLASS_DEFINE__CPP except\n\t' + str(e))
                            try: # bug fix @ 190722
                                classname = classname[:classname.index(r'{')]
                            except Exception as e:
                                print('PATTERN_CLASS_DEFINE__CPP except\n\t' + str(e))
                            if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                ns = ns_util.getNamespace()
                                nd = TreeNode(classname, filepath, ns)
                                line_h_classid = nd.get_id()
                                list_classid_def__cpp.append(line_h_classid)
                                dict_filename_classid__cpp[filename] = line_h_classid
                                if line_h_classid not in dict_classid_treenode__cpp.keys():
                                    dict_classid_treenode__cpp[line_h_classid] = nd
                                    dict_classid_filename__cpp[line_h_classid] = filename
                                    set_classname__cpp.add(classname)
                                    key_class_id = line_h_classid if classname == key_class else key_class_id
                            break
                    f.close()
    print('='*10 + '\tmapping of filename - class id begin\t' + '='*10)
    print('-'*10 + '\tjava\t' + '-'*10)
    for filename in dict_filename_classid:
        print(filename + ' : ' + dict_filename_classid[filename])
    print('-'*10 + '\tc++\t' + '-'*10)
    for filename in dict_filename_classid__cpp:
        print(filename + ' : ' + dict_filename_classid__cpp[filename])
    print('='*10 + '\tmapping of filename - class id end\t' + '='*10)
    if (len(dict_classid_treenode) > 0 or len(dict_classid_treenode__cpp) > 0) and mode.find('r') >= 0:
        for root_dir in sRootDir:
            for root, subdirs, files in os.walk(root_dir):
                print('tree \t' + str(files))
                for filename in files:
                    if filename.find('.java') > 0:
                        filepath = os.path.join(root, filename)
                        print('parsing class relationship in \t' + filepath)
                        f = open(filepath, 'r')
                        buff = f.read()
                        buff = re.sub(PATTERN_CLASS_DEFINE + '.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_WITH_PARENT + '.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_IMPLEMENT_INTERFACE + '.*\n?', '', buff)
                        buff = re.sub(r'import ' + '.*\n?', '', buff)
                        f.close()
                        set_reliedclassid = set()

                        fclassid = dict_filename_classid.get(filename)

                        if fclassid is None:
                            print('skip due to no class defined in ' + filename)
                            continue

                        if fclassid not in dict_classid_treenode:
                            print('should not happen [' + filename + ' [' + fclassid)
                            # nd = TreeNode(fclassid, filepath)
                            # dict_classid_treenode[fclassid] = nd
                            # key_class_id = line_classid if classname == key_class else key_class_id
                            # set_classname.add(nd.get_classname())
                        nd_fclassid = dict_classid_treenode.get(fclassid)

                        for clzid in dict_classid_treenode:
                            clz = dict_classid_treenode.get(clzid).get_classname()
                            pat = r"\ " + clz + r"\.|new\ " + clz + r"|\"[a-zA-Z]+\." + clz + r"\"" + r"|"+ clz + "\ +[a-zA-Z_]+\ +=" + r"|" + clz + r"\.class"
                            #print('debug : ' + pat)
                            # \ Intent\.|new Intent
                            if re.search(pat, buff):
                                set_reliedclassid.add(clzid)
                                # clz's node has created already
                                nd_clz = dict_classid_treenode.get(clzid)
                                print('\t find relied class ' + nd_clz.get_classname())
                                nd_clz.add_lchild(fclassid)
                                nd_fclassid.add_rchild(clzid)
                        dict_classid_reliedclass[fclassid] = set_reliedclassid
                        if len(set_reliedclassid) < 1:
                            print('\t no relied class')
                    elif filename.endswith('.h'):
                        filepath = os.path.join(root, filename)
                        print('parsing class relationship in \t'+ filename + ' : ' + filepath)
                        f = open(filepath, 'r')
                        buff = f.read()
                        buff = re.sub(PATTERN_CLASS_DEFINE__CPP + '.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_WITH_PARENT__CPP + '.*\n?', '', buff)
                        buff = re.sub(r'include ' + '.*\n?', '', buff)
                        f.close()
                        set_reliedclassid = set()

                        fclassid = dict_filename_classid__cpp.get(filename)

                        if fclassid is None:
                            print('skip due to no class defined in ' + filename)
                            continue

                        if fclassid not in dict_classid_treenode__cpp:
                            nd = TreeNode(fclassid, filepath)
                            dict_classid_treenode__cpp[fclassid] = nd
                            set_classname__cpp.add(nd.get_classname())
                        nd_fclassid = dict_classid_treenode__cpp.get(fclassid)

                        if dict_classid_reliedclassidSet__cpp.get(fclassid) is not None:
                            set_reliedclassid = dict_classid_reliedclassidSet__cpp.get(fclassid)

                        for clzid in dict_classid_treenode__cpp:
                            clz = dict_classid_treenode__cpp.get(clzid).get_classname()
                            pat = r'\ *' + clz + r'(<\w+>)?' + r'\ *' + r'\*?' + r'\ *' + r'\w+' + r'\ *\w+\ *;' # member defined in header file
                            # \ Intent\.|new Intent
                            if re.search(pat, buff):
                                set_reliedclassid.add(clzid)
                                # clz's node has created already
                                nd_clz = dict_classid_treenode__cpp.get(clzid)
                                print('\t find relied class (member ship) ' + nd_clz.get_classname())
                                nd_clz.add_lchild(fclassid)
                                nd_fclassid.add_rchild(clzid)
                        dict_classid_reliedclassidSet__cpp[fclassid] = set_reliedclassid
                        if len(set_reliedclassid) < 1:
                            print('\t no relied class')
                    elif filename.endswith('.cpp'):
                        filepath = os.path.join(root, filename)
                        print('parsing class relationship in \t'+ filename + ' : ' + filepath)
                        f = open(filepath, 'r')
                        buff = f.read()
                        buff = re.sub(PATTERN_CLASS_DEFINE__CPP + '.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_WITH_PARENT__CPP + '.*\n?', '', buff)
                        buff = re.sub(r'include ' + '.*\n?', '', buff)
                        f.close()

                        set_reliedclassid = set()
                        ismaincpp = False

                        # [TODO] we simply suppose header file always has same file name with cpp
                        fclassid = dict_filename_classid__cpp.get(filename.replace(r'.cpp', r'.h'))

                        if fclassid is None:
                            # check if it's the main entry cpp file
                            #   - int main(
                            pat = r'int\ +main\ *\('
                            if re.search(pat, buff):
                                ismaincpp = True
                                fclassid = filename.replace(r'.cpp', r'_cpp')
                                if fclassid in excluded_class:
                                    print('skip due to ' + fclassid + ' is excluded')
                                    continue
                            else:
                                print('skip due to no class defined in ' + filename)
                                continue
                        else:
                            print('\t checking class ' + fclassid)

                        if fclassid not in dict_classid_treenode__cpp:
                            nd = TreeNode(fclassid, filepath)
                            dict_classid_treenode__cpp[fclassid] = nd
                            set_classname__cpp.add(nd.get_classname())
                        nd_fclassid = dict_classid_treenode__cpp.get(fclassid)

                        if dict_classid_reliedclassidSet__cpp.get(fclassid) is not None:
                            set_reliedclassid = dict_classid_reliedclassidSet__cpp.get(fclassid)

                        for clz_id in dict_classid_treenode__cpp:
                            clz = dict_classid_treenode__cpp.get(clz_id).get_classname()
                            pat = r'new\ +' + r'(\w*::)?' + clz # new class instance in cpp
                                                                # only care about new instance, as invoke relation ship is to complex
                            if ismaincpp:
                                pat = pat + r'|' + clz + r'::' + r'|' + clz + r'\ +' + r'|' + r'<' + clz + r'>'
                            # \ Intent\.|new Intent
                            if re.search(pat, buff) and clz != nd_fclassid.get_classname():
                                set_reliedclassid.add(clz_id)
                                # clz's node has created already
                                nd_clz = dict_classid_treenode__cpp.get(clz_id)
                                print('\t find relied class (new instance) ' + nd_clz.name)
                                nd_clz.add_lchild(fclassid)
                                nd_fclassid.add_rchild(clz_id)
                        dict_classid_reliedclassidSet__cpp[fclassid] = set_reliedclassid
                        if len(set_reliedclassid) < 1:
                            print('\t no relied class')

    #print(dict_classid_reliedclass)
    mClzRelationShips = ClzRelationShips()
    mClzRelationShips.set_var("root_dir", list(sRootDir)[0])
    mClzRelationShips.set_var("dict_classid_parentid", dict_classid_parentid)
    mClzRelationShips.set_var("dict_classid_interfaceid", dict_classid_interfaceid)
    mClzRelationShips.set_var("dict_classid_reliedclass", dict_classid_reliedclass)
    mClzRelationShips.set_var("dict_classid_treenode", dict_classid_treenode)
    mClzRelationShips.set_var("set_classname", set_classname)
    mClzRelationShips.set_var("key_class", key_class)
    mClzRelationShips.set_var("key_class_id", key_class_id)
    if key_class is not None:
        print(dict_classid_treenode.get(key_class_id))
        print('key class [' + key_class + '] with id [' + key_class_id + '] with class info [')
    mClzRelationShips.set_var("depth", depth)
    mClzRelationShips.set_var("lang", "java")
    if len(dict_classid_treenode) > 0:
        draw_class_relationship(mClzRelationShips)
    if len(dict_classid_treenode__cpp) > 0:
        mClzRelationShips.set_var("dict_classid_parentid", dict_classid_parentid__cpp)
        mClzRelationShips.set_var("dict_classid_reliedclass", dict_classid_reliedclassidSet__cpp)
        mClzRelationShips.set_var("dict_classid_treenode", dict_classid_treenode__cpp)
        mClzRelationShips.set_var("set_classname", set_classname__cpp)
        mClzRelationShips.set_var("lang", "cpp")
        draw_class_relationship(mClzRelationShips)
    if debug:
        print('dump ===================================================')
        dump(dict_classid_treenode)
        print('dump ===================================================')
        dump(dict_classid_treenode__cpp)


def main(sRootDir, mode, included_java_class, included_cpp_class, excluded_class, key_class, depth):
    scan_class_define(sRootDir, mode, included_java_class, included_cpp_class, excluded_class, key_class, depth)


def print_help():
    print('''
v1.0

Usage: python scan_clazz.py -p dir_to_scan [options]

    Options:
    -m mode
            mode can be 'c' 'i' 'r', or combine
            'c' - parsing class and inherit
            'i' - parsing interface and implement (NOT supported)
            'r' - parsing relationship between classes (used by)
    -ij class[,class2,class3,...,classn]
            include additional java classes
            for example, include additional framework calss when scanning packages app
    -ic class[,class2,class3,...,classn]
            include additional cpp classes
            for example, include additional framework calss when scanning packages app
    -e class[,class2,class3,...,classn]
            exclude classes in parsing result
    -k class
            assign the key class which will be emphasized in output
    -d depth
            take effect only if key class is assigned
            valid depth must be a integer between [3-9], include 3 and 9
            otherwise depth will be discarded
            depth is calculated from key class, a class direct rely on / relied by key class has depth 1 

Feature Support:
    support multiple -p in 1.0+
    ''')


if __name__ == '__main__':
    CACHED_INFO.append('\nscan cmd\n\t' + ' '.join(sys.argv))

    root_dir = None
    sRootDir = set()
    mode = 'ci'  # class inherit + interface implement
                 # possible value : mix of below values
                 #   - 'c' : class
                 #   - 'i' : interface
                 #   - 'r' : rely
    included_java_class = []
    included_cpp_class = []
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
                    sRootDir.add(root_dir)
                except:
                    break
            elif argv == '-m':
                try:
                    mode = sys.argv[i + 1]
                except:
                    pass
            elif argv == '-ij':  # included java class, split with ','
                try:
                    included_java_class = sys.argv[i + 1].split(',')
                    print('user passed included additional java class list : ' + str(included_java_class))
                except:
                    pass
            elif argv == '-ic':  # included cpp class, split with ','
                try:
                    included_cpp_class = sys.argv[i + 1].split(',')
                    print('user passed included additional cpp class list : ' + str(included_cpp_class))
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
                    if depth < 1 or depth > 9:
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

    if len(sRootDir) > 0:
        excluded_class = CLASS_EXCLUDED_ALWAYS + excluded_class
        print('final excluded class list : ' + str(excluded_class))
        main(sRootDir, mode, included_java_class, included_cpp_class, excluded_class, key_class, depth)
    else:
        print('pls assign root dir to scan with -p')
    os._exit(0)
