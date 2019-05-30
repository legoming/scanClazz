# -*- coding: utf-8 -*-

import os
import sys
import re

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


def draw_class_relationship(dict_class_parent, list_class_def, dict_class_reliedclass, set_class_not_standalone):
    set_defined_classes = set()
    if len(dict_class_parent) > 0:
        fo = open('output', 'w')
        #fo.write('```graphviz')
        fo.write('\ndigraph G {')
        if dict_class_parent is not None and len(dict_class_parent) > 0:
            for cls in dict_class_parent:
                if cls is not None and dict_class_parent[cls] is not None:
                    cls_converted = cls.replace('.', '・').replace('<', '‹').replace('>', '›')
                    pnt_converted = dict_class_parent[cls].replace('.', '・').replace('<', '‹').replace('>', '›')
                    if cls not in set_defined_classes:
                        fo.write('\n    ' + cls_converted + '[shape = note]')
                        set_defined_classes.add(cls)
                    if dict_class_parent[cls] not in set_defined_classes:
                        fo.write('\n    ' + pnt_converted + '[shape = component]')
                        set_defined_classes.add(dict_class_parent[cls])
                    fo.write('\n    ' + cls_converted + ' -> ' + pnt_converted + '[arrowhead = empty color=purple]')
                    fo.write('\n')
        if list_class_def is not None and len(list_class_def) > 0:
            if cls is not None:
                for cls in list_class_def:
                    if cls not in set_defined_classes and cls in set_class_not_standalone:
                        cls_converted = cls.replace('.', '・').replace('<', '‹').replace('>', '›')
                        fo.write('\n    ' + cls_converted + '[shape = note]')
                        set_defined_classes.add(cls)
                    elif cls not in set_class_not_standalone:
                        print(cls + ' is standalone' )
        if dict_class_reliedclass is not None and len(dict_class_reliedclass) > 0:
            for cls in dict_class_reliedclass:
                if cls is not None:
                    cls_converted = cls.replace('.', '・').replace('<', '‹').replace('>', '›')
                    if dict_class_reliedclass is not None:
                        for relatedcls in dict_class_reliedclass.get(cls):
                            if relatedcls != cls:
                                relatedcls_converted = relatedcls.replace('.', '・').replace('<', '‹').replace('>', '›')
                                fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
        fo.write('\n}')
        #fo.write('\n```')
        fo.close()


def scan_class_define(root_dir, mode, excluded_class):
    dict_filename_classname = {}
    dict_class_parent = {}
    list_class_def = []
    dict_class_reliedclass = {}
    set_class_not_standalone = set()
    for root, subdirs, files in os.walk(root_dir):
        for filename in files:
            if filename.find('.java') > 0:
                filepath = os.path.join(root, filename)
                f = open(filepath, 'r')

                set_importedclass = set()

                for line in f:
                    if line.startswith('import'):
                        pass
                    elif re.match(PATTERN_CLASS_WITH_PARENT, line):
                        #print(line)
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
                            if len(classname) > 0 and len(parentname) > 0 \
                                    and classname not in excluded_class \
                                    and parentname not in excluded_class:
                                dict_class_parent[classname] = parentname
                                dict_filename_classname[filename] = classname
                                set_class_not_standalone.add(classname)
                                set_class_not_standalone.add(parentname)
                        except:
                            pass
                        break
                    elif re.match(PATTERN_CLASS_DEFINE, line):
                        classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                        try:
                            classname = classname[:classname.index(r' ')]
                        except:
                            pass
                        if classname not in excluded_class:
                            list_class_def.append(classname)
                            dict_filename_classname[filename] = classname
                        break
                f.close()
    if len(list_class_def) > 0 and mode.find('r') >= 0:
        for root, subdirs, files in os.walk(root_dir):
            for filename in files:
                if filename.find('.java') > 0:
                    filepath = os.path.join(root, filename)
                    print(filename + ' : ' + filepath)
                    f = open(filepath, 'r')
                    buff = f.read()
                    f.close()
                    set_importedclass = set()

                    for clz in list_class_def:
                        pat = r"\ " + clz + r"\.|new\ " + clz
                        # \ Intent\.|new Intent
                        if re.search(pat, buff):
                            set_importedclass.add(clz)
                            set_class_not_standalone.add(clz)
                    dict_class_reliedclass[dict_filename_classname.get(filename)] = set_importedclass
                    if len(set_importedclass) > 0:
                        set_class_not_standalone.add(dict_filename_classname.get(filename))
    #print(dict_class_reliedclass)
    draw_class_relationship(dict_class_parent, list_class_def, dict_class_reliedclass, set_class_not_standalone)


def main(root_dir, mode, excluded_class):
    scan_class_define(root_dir, mode, excluded_class)


if __name__ == '__main__':
    root_dir = None
    mode = 'ci' # class inherit + interface implement
                # possible value : mix of below values
                #   - 'c' : class, forced, cannot disable
                #   - 'i' : interface
                #   - 'r' : rely
    excluded_class = []
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
    else:
        # test only
        #main('/Users/lego/workspace/omadm') # scanning in current directory
        root_dir = '/Users/lego/workspace/OTAProvisioningClient'
        #main('/Users/lego/aosp/packages/apps/Settings/src')

    if root_dir is not None:
        main(root_dir, mode, excluded_class)
    else:
        print('pls assign root dir to scan with -p')
    exit(0)
