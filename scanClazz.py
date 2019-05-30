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


def __init__():
    pass


def draw_class_relationship(dict_class_parent):
    if len(dict_class_parent) > 0:
        fo = open('output', 'w')
        #fo.write('```graphviz')
        fo.write('\ndigraph G {')
        for cls in dict_class_parent:
            cls = cls.replace('.', '・').replace('<', '‹').replace('>', '›')
            pnt = dict_class_parent[cls].replace('.', '・').replace('<', '‹').replace('>', '›')
            fo.write('\n    ' + cls + '[shape = plain]')
            fo.write('\n    ' + pnt + '[shape = component]')
            fo.write('\n    ' + cls + ' -> ' + pnt + '[arrowhead = empty]')
            fo.write('\n')
        fo.write('\n}')
        #fo.write('\n```')
        fo.close()


def scan_class_with_parent(root_dir):
    dict_class_parent = {}
    for root, subdirs, files in os.walk(root_dir):
        for filename in files:
            if filename.find('.java') > 0:
                filepath = os.path.join(root, filename)
                f = open(filepath, 'r')

                for line in f:
                    if re.match(PATTERN_CLASS_WITH_PARENT, line):
                        print(line)
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
                        except:
                            pass
                        break
                f.close()
    draw_class_relationship(dict_class_parent)


def main(root_dir):
    scan_class_with_parent(root_dir)


if __name__ == '__main__':
    print('\n' + PATTERN_CLASS_WITH_PARENT + '\n'*3)
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        #main('/Users/lego/workspace/omadm') # scanning in current directory
        main('/Users/lego/workspace/OTAProvisioningClient')
