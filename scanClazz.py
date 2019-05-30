# -*- coding: utf-8 -*-

import os
import sys
import re
from typing import Set

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


def draw_class_relationship(dict_class_parent, list_class_def, dict_class_importedclass):
    if len(dict_class_parent) > 0:
        fo = open('output', 'w')
        #fo.write('```graphviz')
        fo.write('\ndigraph G {')
        for cls in dict_class_parent:
            cls = cls.replace('.', '・').replace('<', '‹').replace('>', '›')
            pnt = dict_class_parent[cls].replace('.', '・').replace('<', '‹').replace('>', '›')
            fo.write('\n    ' + cls + '[shape = note]')
            fo.write('\n    ' + pnt + '[shape = component]')
            fo.write('\n    ' + cls + ' -> ' + pnt + '[arrowhead = empty]')
            fo.write('\n')
        for cls in list_class_def:
            fo.write('\n    ' + cls + '[shape = note]')
        for cls in dict_class_importedclass:
            if cls is not None:
                cls_converted = cls.replace('.', '・').replace('<', '‹').replace('>', '›')
                if dict_class_importedclass is not None:
                    for relatedcls in dict_class_importedclass.get(cls):
                        if relatedcls != cls:
                            relatedcls_converted = relatedcls.replace('.', '・').replace('<', '‹').replace('>', '›')
                            fo.write('\n    ' + cls_converted + ' -> ' + relatedcls_converted + '[style = dashed]')
        fo.write('\n}')
        #fo.write('\n```')
        fo.close()


def scan_class_define(root_dir):
    dict_filename_classname = {}
    dict_class_parent = {}
    list_class_def = []
    dict_class_importedclass = {}
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
                            if len(classname) > 0 and len(parentname) > 0:
                                dict_class_parent[classname] = parentname
                                dict_filename_classname[filename] = classname
                        except:
                            pass
                        break
                    elif re.match(PATTERN_CLASS_DEFINE, line):
                        classname = re.search(KEYWORD_CLASS + '(.*)', line).group(1).strip()
                        try:
                            classname = classname[:classname.index(r' ')]
                        except:
                            pass
                        list_class_def.append(classname)
                        dict_filename_classname[filename] = classname
                        break
                f.close()
    for root, subdirs, files in os.walk(root_dir):
        for filename in files:
            if filename.find('.java') > 0:
                filepath = os.path.join(root, filename)
                f = open(filepath, 'r')

                set_importedclass: Set[str] = set()

                for line in f:
                    for clz in list_class_def:
                        pat = r"\ " + clz + r"\.|new\ " + clz
                        # \ Intent\.|new Intent
                        if re.search(pat, line):
                            set_importedclass.add(clz)
                dict_class_importedclass[dict_filename_classname.get(filename)] = set_importedclass
                f.close()
    #print(dict_class_importedclass)
    draw_class_relationship(dict_class_parent, list_class_def, dict_class_importedclass)


def main(root_dir):
    scan_class_define(root_dir)


if __name__ == '__main__':
    print('\n' + PATTERN_CLASS_WITH_PARENT + '\n'*3)
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        #main('/Users/lego/workspace/omadm') # scanning in current directory
        #main('/Users/lego/workspace/OTAProvisioningClient')
        main('/Users/lego/aosp/packages/apps/Settings/src')
