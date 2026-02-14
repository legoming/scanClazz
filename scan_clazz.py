# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
import shutil
import logging

# configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

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
        input = os.path.abspath(input)
        logging.info('graphviz input file: %s (lang=%s)', input, lang)
        if not os.path.exists(input):
            logging.error('graphviz input does not exist: %s', input)
            return
        try:
            with open(input, 'r', encoding='utf-8', errors='ignore') as fh:
                head = ''.join([next(fh) for _ in range(4)])
            logging.debug('dot head:\n%s', head)
        except Exception:
            logging.debug('unable to read head of %s', input)
        dot_path = shutil.which('dot')
        fdp_path = shutil.which('fdp')
        dot_support = dot_path is not None
        fdp_support = fdp_path is not None

        if not (dot_support or fdp_support):
            logging.debug('No graphviz (dot/fdp) found on PATH')
            return

        logging.info('try to draw png with local installed graphviz')
        outpath = os.path.join(os.path.expanduser("~"), 'Downloads')
        os.makedirs(outpath, exist_ok=True)

        if dot_support:
            try:
                logging.info('running dot on %s -> %s', input, os.path.join(outpath, lang + 'graph-dot.png'))
                proc = subprocess.run([dot_path, input, '-Gdpi=300', '-T', 'png', '-o', os.path.join(outpath, lang + 'graph-dot.png')], check=False, capture_output=True, text=True)
                if proc.returncode == 0:
                    logging.info('dot png: %s', os.path.join(outpath, lang + 'graph-dot.png'))
                else:
                    logging.error('dot failed (returncode=%s) for %s; stderr:\n%s', proc.returncode, input, proc.stderr)
            except Exception as e:
                logging.debug('dot run failed: %s', e)
        if fdp_support:
            try:
                logging.info('running fdp on %s -> %s', input, os.path.join(outpath, lang + 'graph-fdp.png'))
                proc = subprocess.run([fdp_path, input, '-Gdpi=300', '-T', 'png', '-o', os.path.join(outpath, lang + 'graph-fdp.png')], check=False, capture_output=True, text=True)
                if proc.returncode == 0:
                    logging.info('fdp png: %s', os.path.join(outpath, lang + 'graph-fdp.png'))
                else:
                    logging.error('fdp failed (returncode=%s) for %s; stderr:\n%s', proc.returncode, input, proc.stderr)
            except Exception as e:
                logging.debug('fdp run failed: %s', e)
    except Exception as e:
        logging.debug('do_real_draw_if_possible get %s', e)
    logging.debug('\n\n')


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

        out_file_path = os.path.join(root_dir, lang + 'output')
        with open(out_file_path, 'w', encoding='utf-8', errors='ignore') as fo:
            fo.write('# ' + ' '.join(sys.argv))
            #fo.write('```graphviz')
            fo.write('\ndigraph G {')
            # helper to quote/escape identifiers and labels
            def _q(s):
                if s is None:
                    return '""'
                return '"' + str(s).replace('"', '\\"') + '"'
            #fo.write('\nrankdir = LR')

            haskey = True if key_class is not None and key_class in set_classname and key_class_id in dict_classid_treenode else False
            key_nd = dict_classid_treenode.get(key_class_id)
            logging.debug('key_nd = %s', str(key_nd))

            for cls_id in dict_classid_treenode:
                nd = dict_classid_treenode.get(cls_id)
                if nd is not None and nd.is_valid_node():
                    if nd.is_standalone():
                        logging.debug('drop standalone %s', nd.id)
                    elif nd.is_equal(key_class_id):
                        fo.write('\n    ' + _q(nd.displayid) + ' [shape = egg color=green]')
                    elif haskey and not key_nd.is_clz_relate_with_node_in_depth(cls_id, depth, dict_classid_treenode):
                        set_class_depth_exceeded.add(cls_id)
                        CACHED_INFO.append('drop depth exceeded ' + nd.id)
                    elif nd.is_parent():
                        logging.debug('parent node %s', nd.name)
                        label = nd.displayname + r'\n[' + nd.displayns + ']'
                        fo.write('\n    ' + _q(nd.displayid) + ' [shape = plaintext label=' + _q(label) + ']')
                    elif nd.is_interface():
                        logging.debug('interface node %s', nd.name)
                        label = nd.displayname + r'\n[' + nd.displayns + ']'
                        fo.write('\n    ' + _q(nd.displayid) + ' [shape = plaintext label=' + _q(label) + ']')
                    elif nd.is_leaf():
                        label = nd.displayname + r'\n[' + nd.displayns + ']'
                        fo.write('\n    ' + _q(nd.displayid) + ' [shape = plaintext label=' + _q(label) + ']')
                    else:
                        label = nd.displayname + r'\n[' + nd.displayns + ']'
                        fo.write('\n    ' + _q(nd.displayid) + ' [shape = note label=' + _q(label) + ']')
                else:
                    logging.debug('invalid node found')
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
                        fo.write('\n    ' + _q(cls_converted) + ' -> ' + _q(pnt_converted) + ' [arrowhead = empty color=purple]')
            if dict_classid_interfaceid is not None and len(dict_classid_interfaceid) > 0:
                for cls_id in dict_classid_interfaceid:
                    if cls_id not in dict_classid_treenode.keys() or \
                       dict_classid_interfaceid[cls_id] not in dict_classid_treenode.keys():
                        CACHED_INFO.append('skip interface "' + cls_id + '" - -▷ "' + dict_classid_interfaceid[cls_id] + '"')
                        continue
                    if cls_id is not None and dict_classid_interfaceid[cls_id] is not None:
                        cls_converted = dict_classid_treenode.get(cls_id).displayid
                        pnt_converted = dict_classid_treenode.get(dict_classid_interfaceid[cls_id]).displayid
                        fo.write('\n    ' + _q(cls_converted) + ' -> ' + _q(pnt_converted) + ' [arrowhead = empty color=purple style=dashed]')
            if dict_classid_reliedclass is not None and len(dict_classid_reliedclass) > 0:
                for cls_id in dict_classid_reliedclass:
                    if cls_id is not None and cls_id in dict_classid_treenode:
                        cls_converted = dict_classid_treenode.get(cls_id).displayid
                        if dict_classid_reliedclass is not None:
                            for relatedcls in dict_classid_reliedclass.get(cls_id):
                                logging.debug('checking %s \"s relatedcls = %s', cls_id, str(relatedcls))
                                if relatedcls not in dict_classid_treenode:
                                    logging.debug('skipping %s \"s relatedcls = %s', cls_id, str(relatedcls))
                                    CACHED_INFO.append('skip ' + cls_id + ' --> ' + relatedcls)
                                    continue
                                    if relatedcls != cls_id:
                                        relatedcls_converted = dict_classid_treenode.get(relatedcls).displayid
                                        if haskey and \
                                                (key_nd.is_equal(cls_id) or
                                                 key_nd.is_equal(relatedcls)):
                                            logging.debug('writing (key) %s -> %s', cls_id, str(relatedcls))
                                            fo.write('\n    ' + _q(cls_converted) + ' -> ' + _q(relatedcls_converted) + ' [style = dashed]')
                                        elif haskey:
                                            if cls_id not in set_class_depth_exceeded and \
                                               relatedcls not in set_class_depth_exceeded:
                                                logging.debug('writing (near) %s -> %s', cls_id, str(relatedcls))
                                                fo.write('\n    ' + _q(cls_converted) + ' -> ' + _q(relatedcls_converted) + ' [style = dashed color = gray]')
                                            else:
                                                CACHED_INFO.append('drop relationship ' + cls_id + ' --> ' + relatedcls + ' due to depth exceed')
                                        else:
                                            logging.debug('writing %s -> %s', cls_id, str(relatedcls))
                                            fo.write('\n    ' + _q(cls_converted) + ' -> ' + _q(relatedcls_converted) + ' [style = dashed]')
                    else:
                        CACHED_INFO.append('skip ' + cls_id + ' --> ...')
            fo.write('\n}')
            #fo.write('\n```')
        logging.info('wrote graphviz output to %s', out_file_path)
    for ln in CACHED_INFO:
        logging.info(ln)
    logging.info('\noutput: %s/%soutput', root_dir, lang)
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
    logging.debug('getBestPackageName [ %s ] for clz [ %s ]', pkgname, clz)
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
            logging.debug('file tree \t%s', files)
            for filename in files:
                logging.debug('scanning \t%s', filename)
                if filename.endswith('.java'):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
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
                                                nd = TreeNode(classname, filepath, currentPkg, origin='java')
                                                line_classid = nd.get_id()
                                                if line_classid not in dict_classid_treenode.keys():
                                                    dict_classid_treenode[line_classid] = nd
                                                    set_classname.add(classname)
                                                    key_class_id = line_classid if classname == key_class else key_class_id
                                                dict_filename_classid[filename] = line_classid
                                            else:
                                                should_link = False
                                            if mode.find('c') >= 0 and len(parentname) > 0 and fliter_clz(parentname,excluded_class):
                                                nd = TreeNode(parentname, '', parentpkgname[0], origin='java')
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
                                            logging.debug('PATTERN_CLASS_WITH_PARENT except\n\t%s', e)
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
                                                nd = TreeNode(classname, filepath, currentPkg, origin='java')
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
                                                    nd = TreeNode(interface, '', interfacepkgname[0], origin='java')
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
                                            logging.debug('PATTERN_CLASS_IMPLEMENT_INTERFACE except\n\t%s', e)
                                    break
                                elif re.match(PATTERN_CLASS_DEFINE, line):
                                    classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                                    try:
                                        classname = classname[:classname.index(r' ')]
                                    except Exception as e:
                                        logging.debug('PATTERN_CLASS_DEFINE except\n\t%s', e)
                                    if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                        nd = TreeNode(classname, filepath, currentPkg, origin='java')
                                        line_classid = nd.get_id()
                                        list_classid_def.append(line_classid)
                                        dict_filename_classid[filename] = line_classid
                                        if line_classid not in dict_classid_treenode.keys():
                                            dict_classid_treenode[line_classid] = nd
                                            set_classname.add(classname)
                                            key_class_id = line_classid if classname == key_class else key_class_id
                                    break
                    except Exception as e:
                        logging.debug('failed to open java file %s: %s', filepath, e)
                elif filename.endswith('.kt'):
                    # Kotlin source file - robust parser: ignore ':' inside constructor parameter lists or generics
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        currentPkg = ''
                        importedPkgSet = set()

                        def _normalize_kt_type(p):
                            if not p:
                                return ''
                            p = re.sub(r'<.*?>', '', p)  # remove generics
                            p = re.sub(r'\(.*?\)', '', p)  # remove constructor args
                            p = p.split()[0] if p.split() else p
                            p = p.rstrip('?')
                            p = re.sub(r'[^0-9A-Za-z_\.]', '', p)
                            return p

                        def _is_probable_type(name):
                            if not name:
                                return False
                            primitives = {'Int','Long','Float','Double','Boolean','String','Char','Short','Byte','Any','Unit'}
                            keywords = {'var','val','params','override','private','public','internal'}
                            if name in primitives or name in keywords:
                                return False
                            if '.' in name:
                                return True
                            return name[0].isupper()

                        for idx, rawline in enumerate(lines):
                            line = rawline.strip()
                            if len(line) < 1:
                                continue
                            if line.startswith('package'):
                                currentPkg = line.replace('package', '').replace(';', '').strip()
                                continue
                            if line.startswith('import'):
                                importedPkgSet.add(line.replace('import', '').replace(';', '').strip())
                                continue
                            if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
                                continue
                            m = re.search(r"\b(class|interface|object|enum)\s+([A-Za-z_][A-Za-z0-9_\.<>]*)", line)
                            if not m:
                                m = re.search(r"(?:data|sealed|open|abstract|inner|private|public|internal)\s+(class|interface|object|enum)\s+([A-Za-z_][A-Za-z0-9_\.<>]*)", line)
                            # fallback: try a small snippet spanning several following lines (handles annotations or constructor keywords)
                            if not m:
                                snippet = ' '.join([lines[j].strip() for j in range(idx, min(idx+6, len(lines)))])
                                m_snip = re.search(r"\b(class|interface|object|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", snippet)
                                if m_snip:
                                    m = m_snip
                            # fallback: annotation or 'constructor' may appear after classname; try a simpler classname capture
                            if not m:
                                m2 = re.search(r"\b(class|interface|object|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
                                if m2:
                                    m = m2
                            if m:
                                try:
                                    classname = m.group(2)
                                    classname_plain = re.sub(r'<.*?>', '', classname)
                                    rest = line[m.end():]
                                    lookahead = 1
                                    # gather a small snippet ahead; do NOT stop on ':' because constructor params contain ':'
                                    while ('{' not in rest and lookahead <= 8 and idx+lookahead < len(lines)):
                                        rest += ' ' + lines[idx+lookahead].strip()
                                        lookahead += 1
                                    # find ':' that is not inside parentheses or angle brackets
                                    colon_index = -1
                                    paren_depth = 0
                                    angle_depth = 0
                                    for i, ch in enumerate(rest):
                                        if ch == '(':
                                            paren_depth += 1
                                        elif ch == ')':
                                            if paren_depth > 0:
                                                paren_depth -= 1
                                        elif ch == '<':
                                            angle_depth += 1
                                        elif ch == '>':
                                            if angle_depth > 0:
                                                angle_depth -= 1
                                        elif ch == ':' and paren_depth == 0 and angle_depth == 0:
                                            colon_index = i
                                            break
                                    parent_list = []
                                    if colon_index != -1:
                                        parent_part = rest[colon_index+1:]
                                        parent_part = re.split(r'\{|//|\bwhere\b', parent_part, 1)[0]
                                        for p in parent_part.split(','):
                                            p = p.strip()
                                            if not p:
                                                continue
                                            p = _normalize_kt_type(p)
                                            if p:
                                                parent_list.append(p)
                                    should_link = True
                                    if len(classname_plain) > 0 and fliter_clz(classname_plain, excluded_class):
                                        nd = TreeNode(classname_plain, filepath, currentPkg, origin='kotlin')
                                        line_classid = nd.get_id()
                                        logging.debug('kotlin found class %s in %s (id=%s)', classname_plain, filename, line_classid)
                                        if line_classid not in dict_classid_treenode.keys():
                                            dict_classid_treenode[line_classid] = nd
                                            set_classname.add(classname_plain)
                                            key_class_id = line_classid if classname_plain == key_class else key_class_id
                                        dict_filename_classid[filename] = line_classid
                                    else:
                                        should_link = False

                                    if should_link and len(parent_list) > 0 and mode.find('c') >= 0:
                                        # In Kotlin the first entry after ':' (if any) is the superclass (may include constructor args)
                                        # subsequent entries are interfaces. Map them accordingly.
                                        for idx_p, parent in enumerate(parent_list):
                                            if not _is_probable_type(parent):
                                                logging.debug('skip kotlin parent not-a-type: %s', parent)
                                                continue
                                            if not fliter_clz(parent, excluded_class):
                                                continue
                                            parentpkg = getBestPackageName(parent, importedPkgSet, currentPkg)
                                            ndp = TreeNode(parent, '', parentpkg[0], origin='kotlin')
                                            line_parentid = ndp.get_id()
                                            if line_parentid not in dict_classid_treenode.keys():
                                                dict_classid_treenode[line_parentid] = ndp
                                                set_classname.add(parent)
                                                key_class_id = line_parentid if parent == key_class else key_class_id
                                            if idx_p == 0:
                                                # superclass (inherit)
                                                dict_classid_parentid[line_classid] = line_parentid
                                                dict_classid_treenode.get(line_classid).add_parent(line_parentid)
                                                dict_classid_treenode.get(line_parentid).add_child(line_classid)
                                            else:
                                                # interface (implement)
                                                dict_classid_interfaceid[line_classid] = line_parentid
                                                dict_classid_treenode.get(line_classid).add_interface(line_parentid)
                                                dict_classid_treenode.get(line_parentid).add_implement(line_classid)
                                except Exception as e:
                                    logging.debug('Kotlin parse except %s in %s', e, line)
                                # continue scanning after a class declaration
                    except Exception as e:
                        logging.debug('failed to open kotlin file %s: %s', filepath, e)
                elif filename.endswith('.h'):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
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
                                logging.debug('header pre-line: %s', str(line))
                                if re.match(PATTERN_CLASS_WITH_PARENT__CPP, line):
                                    logging.debug('header match: %s', str(line))
                                    try:
                                        classname = re.search(KEYWORD_CLASS + '(.*)' + KEYWORD_EXTEND__CPP, line).group(1).strip()
                                        logging.debug('found class name %s', classname)
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
                                        try:
                                            parentname_multi = parentname_multi.replace(r'virtual ', r'')
                                        except:
                                            pass
                                        should_link = True
                                        if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                            ns = ns_util.getNamespace()
                                            nd = TreeNode(classname, filepath, ns, origin='cpp')
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
                                                    nd = TreeNode(parentname, guessHeaderFromClassName(parentname, includedHeaderSet), origin='cpp')
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
                                                    logging.debug('create inherit relationship [cpp] %s --▷ %s', line_h_classid, line_h_parentid)
                                                else:
                                                    CACHED_INFO.append('drop inherit relationship [cpp] ' + line_h_classid + ' --▷ ' + line_h_parentid)
                                        else:
                                            CACHED_INFO.append('drop inherit relationship [cpp] ' + classname + ' --▷ ' + parentname_multi)
                                        logging.debug('header end: %s', str(line))
                                    except Exception as e:
                                        logging.debug('PATTERN_CLASS_WITH_PARENT__CPP [%s] except\n\t%s\n\t in %s', PATTERN_CLASS_WITH_PARENT__CPP, e, line)
                                    break
                                elif re.match(PATTERN_CLASS_DEFINE__CPP, line):
                                    classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                                    try:
                                        classname = classname[:classname.index(r' ')]
                                    except Exception as e:
                                        logging.debug('PATTERN_CLASS_DEFINE__CPP except\n\t%s', e)
                                    try: # bug fix @ 190722
                                        classname = classname[:classname.index(r'{')]
                                    except Exception as e:
                                        logging.debug('PATTERN_CLASS_DEFINE__CPP except\n\t%s', e)
                                    if len(classname) > 0 and fliter_clz(classname,excluded_class):
                                        ns = ns_util.getNamespace()
                                        nd = TreeNode(classname, filepath, ns, origin='cpp')
                                        line_h_classid = nd.get_id()
                                        list_classid_def__cpp.append(line_h_classid)
                                        dict_filename_classid__cpp[filename] = line_h_classid
                                        if line_h_classid not in dict_classid_treenode__cpp.keys():
                                            dict_classid_treenode__cpp[line_h_classid] = nd
                                            dict_classid_filename__cpp[line_h_classid] = filename
                                            set_classname__cpp.add(classname)
                                            key_class_id = line_h_classid if classname == key_class else key_class_id
                                    break
                    except Exception as e:
                        logging.debug('failed to open header file %s: %s', filepath, e)
                        continue
    logging.info('%s\tmapping of filename - class id begin\t%s', '='*10, '='*10)
    logging.info('%s\tjava\t%s', '-'*10, '-'*10)
    for filename in dict_filename_classid:
        logging.info('%s : %s', filename, dict_filename_classid[filename])
    logging.info('%s\tc++\t%s', '-'*10, '-'*10)
    for filename in dict_filename_classid__cpp:
        logging.info('%s : %s', filename, dict_filename_classid__cpp[filename])
    logging.info('%s\tmapping of filename - class id end\t%s', '='*10, '='*10)
    if (len(dict_classid_treenode) > 0 or len(dict_classid_treenode__cpp) > 0) and mode.find('r') >= 0:
        # Precompile class-related regex patterns to speed up repeated searches
        java_re_map = {}
        cpp_re_map = {}
        if len(dict_classid_treenode) > 0:
            for clzid, nd in dict_classid_treenode.items():
                clz = nd.get_classname()
                if not clz:
                    continue
                # pattern covers usages like: " X.Cls", new Cls, "pkg.Cls", variable declarations, Cls.class, Kotlin ::class
                pat = r"(?:\\s" + re.escape(clz) + r"\\.|new\\s+" + re.escape(clz) + r'|"[A-Za-z]+\\.' + re.escape(clz) + r'"|' + re.escape(clz) + r"\\s+[A-Za-z_]+\\s*=|" + re.escape(clz) + r"\\.class|" + re.escape(clz) + r"::class)"
                try:
                    java_re_map[clzid] = re.compile(pat)
                except re.error:
                    java_re_map[clzid] = re.compile(re.escape(clz))
        if len(dict_classid_treenode__cpp) > 0:
            for clzid, nd in dict_classid_treenode__cpp.items():
                clz = nd.get_classname()
                if not clz:
                    continue
                # cpp member declaration pattern and new-instance pattern
                pat_member = r"\\s*" + re.escape(clz) + r"(<\\w+>)?\\s*\\*?\\s*\\w+\\s*\\w*\\s*;"
                pat_new = r"new\\s+" + r"(\\w*::)?" + re.escape(clz)
                try:
                    cpp_re_map[clzid] = (re.compile(pat_member), re.compile(pat_new))
                except re.error:
                    cpp_re_map[clzid] = (re.compile(re.escape(clz)), re.compile(re.escape(clz)))

        for root_dir in sRootDir:
            for root, subdirs, files in os.walk(root_dir):
                logging.debug('tree \t%s', files)
                for filename in files:
                    if filename.endswith('.java') or filename.endswith('.kt'):
                        filepath = os.path.join(root, filename)
                        logging.debug('parsing class relationship in %s', filepath)
                        try:
                            fsize = os.path.getsize(filepath)
                        except Exception:
                            fsize = 0

                        LARGE_FILE_THRESHOLD = 1_000_000  # 1MB
                        set_reliedclassid = set()

                        if fsize > LARGE_FILE_THRESHOLD:
                            # stream large files line-by-line to avoid huge memory spikes
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                                    for line in fh:
                                        for clzid, cre in java_re_map.items():
                                            if cre.search(line):
                                                set_reliedclassid.add(clzid)
                                                nd_clz = dict_classid_treenode.get(clzid)
                                                logging.info('\t find relied class %s', nd_clz.get_classname())
                                                nd_clz.add_lchild(fclassid)
                                                nd_fclassid.add_rchild(clzid)
                            except Exception as e:
                                logging.debug('failed to stream java file %s: %s', filepath, e)
                                continue
                        else:
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    buff = f.read()
                            except Exception as e:
                                logging.debug('failed to open java file %s: %s', filepath, e)
                                continue
                            # remove java class definition noise to reduce false positives
                            buff = re.sub(PATTERN_CLASS_DEFINE + '.*\n?', '', buff)
                            buff = re.sub(PATTERN_CLASS_WITH_PARENT + '.*\n?', '', buff)
                            buff = re.sub(PATTERN_CLASS_IMPLEMENT_INTERFACE + '.*\n?', '', buff)
                            buff = re.sub(r'import ' + '.*\n?', '', buff)
                            # also remove simple kotlin class declarations to avoid matching within definitions
                            buff = re.sub(r'\b(class|interface|object|enum)\s+[0-9A-Za-z_\.<>]+.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_DEFINE + '.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_WITH_PARENT + '.*\n?', '', buff)
                        buff = re.sub(PATTERN_CLASS_IMPLEMENT_INTERFACE + '.*\n?', '', buff)
                        buff = re.sub(r'import ' + '.*\n?', '', buff)
                        set_reliedclassid = set()

                        fclassid = dict_filename_classid.get(filename)

                        if fclassid is None:
                            logging.debug('skip due to no class defined in %s', filename)
                            continue

                        if fclassid not in dict_classid_treenode:
                            logging.warning('should not happen [%s [%s', filename, fclassid)
                            # nd = TreeNode(fclassid, filepath)
                            # dict_classid_treenode[fclassid] = nd
                            # key_class_id = line_classid if classname == key_class else key_class_id
                            # set_classname.add(nd.get_classname())
                        nd_fclassid = dict_classid_treenode.get(fclassid)

                        for clzid, nd_clz in dict_classid_treenode.items():
                            cre = java_re_map.get(clzid)
                            if cre and cre.search(buff):
                                set_reliedclassid.add(clzid)
                                # clz's node has created already
                                logging.info('\t find relied class %s', nd_clz.get_classname())
                                nd_clz.add_lchild(fclassid)
                                nd_fclassid.add_rchild(clzid)
                        dict_classid_reliedclass[fclassid] = set_reliedclassid
                        if len(set_reliedclassid) < 1:
                            logging.debug('\t no relied class')
                    elif filename.endswith('.h'):
                        filepath = os.path.join(root, filename)
                        logging.debug('parsing class relationship in %s : %s', filename, filepath)
                        try:
                            fsize = os.path.getsize(filepath)
                        except Exception:
                            fsize = 0
                        LARGE_FILE_THRESHOLD = 1_000_000
                        set_reliedclassid = set()
                        if fsize > LARGE_FILE_THRESHOLD:
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                                    for line in fh:
                                        for clzid, patterns in cpp_re_map.items():
                                            pat_member = patterns[0]
                                            if pat_member.search(line):
                                                set_reliedclassid.add(clzid)
                                                nd_clz = dict_classid_treenode__cpp.get(clzid)
                                                logging.info('\t find relied class (member ship) %s', nd_clz.get_classname())
                                                nd_clz.add_lchild(fclassid)
                                                nd_fclassid.add_rchild(clzid)
                            except Exception as e:
                                logging.debug('failed to stream header file %s: %s', filepath, e)
                                continue
                        else:
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    buff = f.read()
                            except Exception as e:
                                logging.debug('failed to open header file %s: %s', filepath, e)
                                continue
                            buff = re.sub(PATTERN_CLASS_DEFINE__CPP + '.*\n?', '', buff)
                            buff = re.sub(PATTERN_CLASS_WITH_PARENT__CPP + '.*\n?', '', buff)
                            buff = re.sub(r'include ' + '.*\n?', '', buff)

                        fclassid = dict_filename_classid__cpp.get(filename)

                        if fclassid is None:
                            logging.debug('skip due to no class defined in %s', filename)
                            continue

                        if fclassid not in dict_classid_treenode__cpp:
                            nd = TreeNode(fclassid, filepath, origin='cpp')
                            dict_classid_treenode__cpp[fclassid] = nd
                            set_classname__cpp.add(nd.get_classname())
                        nd_fclassid = dict_classid_treenode__cpp.get(fclassid)

                        if dict_classid_reliedclassidSet__cpp.get(fclassid) is not None:
                            set_reliedclassid = dict_classid_reliedclassidSet__cpp.get(fclassid)

                        for clzid, nd_clz in dict_classid_treenode__cpp.items():
                            patterns = cpp_re_map.get(clzid)
                            if patterns:
                                pat_member, _ = patterns
                                if pat_member.search(buff):
                                    set_reliedclassid.add(clzid)
                                    logging.info('\t find relied class (member ship) %s', nd_clz.get_classname())
                                    nd_clz.add_lchild(fclassid)
                                    nd_fclassid.add_rchild(clzid)
                        dict_classid_reliedclassidSet__cpp[fclassid] = set_reliedclassid
                        if len(set_reliedclassid) < 1:
                            logging.debug('\t no relied class')
                    elif filename.endswith('.cpp'):
                        filepath = os.path.join(root, filename)
                        logging.debug('parsing class relationship in %s : %s', filename, filepath)
                        try:
                            fsize = os.path.getsize(filepath)
                        except Exception:
                            fsize = 0
                        LARGE_FILE_THRESHOLD = 1_000_000
                        set_reliedclassid = set()
                        ismaincpp = False
                        if fsize > LARGE_FILE_THRESHOLD:
                            # stream large cpp files
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                                    buff_lines = fh.readlines()
                            except Exception as e:
                                logging.debug('failed to stream cpp file %s: %s', filepath, e)
                                continue
                        else:
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    buff = f.read()
                            except Exception as e:
                                logging.debug('failed to open cpp file %s: %s', filepath, e)
                                continue
                            buff = re.sub(PATTERN_CLASS_DEFINE__CPP + '.*\n?', '', buff)
                            buff = re.sub(PATTERN_CLASS_WITH_PARENT__CPP + '.*\n?', '', buff)
                            buff = re.sub(r'include ' + '.*\n?', '', buff)

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
                                    logging.debug('skip due to %s is excluded', fclassid)
                                    continue
                            else:
                                logging.debug('skip due to no class defined in %s', filename)
                                continue
                        else:
                            logging.debug('\t checking class %s', fclassid)

                        if fclassid not in dict_classid_treenode__cpp:
                            nd = TreeNode(fclassid, filepath, origin='cpp')
                            dict_classid_treenode__cpp[fclassid] = nd
                            set_classname__cpp.add(nd.get_classname())
                        nd_fclassid = dict_classid_treenode__cpp.get(fclassid)

                        if dict_classid_reliedclassidSet__cpp.get(fclassid) is not None:
                            set_reliedclassid = dict_classid_reliedclassidSet__cpp.get(fclassid)

                        for clz_id, nd_clz in dict_classid_treenode__cpp.items():
                            patterns = cpp_re_map.get(clz_id)
                            pat_new = patterns[1] if patterns else None
                            if pat_new and pat_new.search(buff) and nd_clz.get_classname() != nd_fclassid.get_classname():
                                set_reliedclassid.add(clz_id)
                                # clz's node has created already
                                logging.info('\t find relied class (new instance) %s', nd_clz.get_classname())
                                nd_clz.add_lchild(fclassid)
                                nd_fclassid.add_rchild(clz_id)
                        dict_classid_reliedclassidSet__cpp[fclassid] = set_reliedclassid
                        if len(set_reliedclassid) < 1:
                            logging.debug('\t no relied class')

    # debug: dict_classid_reliedclass
    mClzRelationShips = ClzRelationShips()
    mClzRelationShips.set_var("root_dir", list(sRootDir)[0])
    # split Java vs Kotlin nodes so the Java graph doesn't include .kt-derived nodes
    java_nodes = {k: v for k, v in dict_classid_treenode.items() if not (v.file or '').lower().endswith('.kt')}
    if len(java_nodes) == 0:
        # fallback: if no java-only nodes, keep original behavior
        java_nodes = dict_classid_treenode
    # filter parent/interface/relied maps to only include java nodes
    def _filter_map_single(src_map, nodes):
        if not src_map:
            return {}
        return {k: v for k, v in src_map.items() if k in nodes and v in nodes}

    def _filter_map_set(src_map, nodes):
        if not src_map:
            return {}
        out = {}
        for k, s in src_map.items():
            if k not in nodes:
                continue
            filtered = {x for x in s if x in nodes}
            if filtered:
                out[k] = filtered
        return out

    dict_classid_parentid_java = _filter_map_single(dict_classid_parentid, java_nodes)
    dict_classid_interfaceid_java = _filter_map_single(dict_classid_interfaceid, java_nodes)
    dict_classid_reliedclass_java = _filter_map_set(dict_classid_reliedclass, java_nodes)

    mClzRelationShips.set_var("dict_classid_parentid", dict_classid_parentid_java)
    mClzRelationShips.set_var("dict_classid_interfaceid", dict_classid_interfaceid_java)
    mClzRelationShips.set_var("dict_classid_reliedclass", dict_classid_reliedclass_java)
    mClzRelationShips.set_var("dict_classid_treenode", java_nodes)
    mClzRelationShips.set_var("set_classname", {nd.get_classname() for nd in java_nodes.values()})
    mClzRelationShips.set_var("key_class", key_class)
    mClzRelationShips.set_var("key_class_id", key_class_id if key_class_id in java_nodes else None)
    if key_class is not None:
        logging.info('%s', dict_classid_treenode.get(key_class_id))
        logging.info('key class [%s] with id [%s] with class info [', key_class, key_class_id)
    mClzRelationShips.set_var("depth", depth)
    mClzRelationShips.set_var("lang", "java")
    if len(dict_classid_treenode) > 0:
        draw_class_relationship(mClzRelationShips)
    # if there are Kotlin files, produce a separate Kotlin graph (ktgraph-dot.png / ktgraph-fdp.png)
    # prefer explicit origin if available
    kt_nodes = {k: v for k, v in dict_classid_treenode.items() if getattr(v, 'origin', None) == 'kotlin' or (v.file or '').lower().endswith('.kt')}
    if len(kt_nodes) > 0:
            mClzKt = ClzRelationShips()
            mClzKt.set_var("root_dir", list(sRootDir)[0])
            mClzKt.set_var("dict_classid_parentid", dict_classid_parentid)
            mClzKt.set_var("dict_classid_interfaceid", dict_classid_interfaceid)
            mClzKt.set_var("dict_classid_reliedclass", dict_classid_reliedclass)
            mClzKt.set_var("dict_classid_treenode", kt_nodes)
            mClzKt.set_var("set_classname", set([nd.get_classname() for nd in kt_nodes.values()]))
            mClzKt.set_var("key_class", key_class)
            # if key_class_id not in kt_nodes, set to None to avoid highlighting
            mClzKt.set_var("key_class_id", key_class_id if key_class_id in kt_nodes else None)
            mClzKt.set_var("depth", depth)
            mClzKt.set_var("lang", "kt")
            draw_class_relationship(mClzKt)
    if len(dict_classid_treenode__cpp) > 0:
        mClzRelationShips.set_var("dict_classid_parentid", dict_classid_parentid__cpp)
        mClzRelationShips.set_var("dict_classid_reliedclass", dict_classid_reliedclassidSet__cpp)
        mClzRelationShips.set_var("dict_classid_treenode", dict_classid_treenode__cpp)
        mClzRelationShips.set_var("set_classname", set_classname__cpp)
        mClzRelationShips.set_var("lang", "cpp")
        draw_class_relationship(mClzRelationShips)
    if debug:
        logging.debug('dump ===================================================')
        dump(dict_classid_treenode)
        logging.debug('dump ===================================================')
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
                sys.exit(0)
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
                    logging.info('user passed included additional java class list : %s', str(included_java_class))
                except:
                    pass
            elif argv == '-ic':  # included cpp class, split with ','
                try:
                    included_cpp_class = sys.argv[i + 1].split(',')
                    logging.info('user passed included additional cpp class list : %s', str(included_cpp_class))
                except:
                    pass
            elif argv == '-e':  # excluded class, split with ','
                try:
                    excluded_class = sys.argv[i + 1].split(',')
                    logging.info('user passed excluded class list : %s', str(excluded_class))
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
        sys.exit(0)

    if key_class is None and (2 < depth < 10):
        depth = -1
        CACHED_INFO.append('depth ' + str(depth) + ' is dropped as key class is not assigned')

    if len(sRootDir) > 0:
        excluded_class = CLASS_EXCLUDED_ALWAYS + excluded_class
        logging.info('final excluded class list : %s', str(excluded_class))
        main(sRootDir, mode, included_java_class, included_cpp_class, excluded_class, key_class, depth)
    else:
        logging.error('pls assign root dir to scan with -p')
        sys.exit(0)
