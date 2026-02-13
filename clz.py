# -*- coding: utf-8 -*-

DicArgvTypes = {
        "root_dir" : "<class 'str'>", 
        "sRootDir" : "<class 'set'>",
        "dict_classid_parentid" : "<class 'dict'>", 
        "dict_classid_interfaceid" : "<class 'dict'>",
        "dict_classid_reliedclass" : "<class 'dict'>", 
        "dict_classid_treenode" : "<class 'dict'>", 
        "set_classname" : "<class 'set'>",
        "key_class" : "<class 'str'>", 
        "key_class_id" : "<class 'str'>", 
        "depth" : "<class 'int'>", 
        "lang" : "<class 'str'>"}

class ClzRelationShips:

    def __init__(self):
        # root_dir, dict_class_parent, dict_class_reliedclass, dict_classname_treenode, key_class, depth, type
        self.argvs = {}

    def set_var(self, arg_type, arg_value):
        if arg_type in DicArgvTypes.keys() and str(type(arg_value)) == DicArgvTypes.get(arg_type):
            self.argvs[arg_type] = arg_value
        else:
            import logging
            logging.debug(str(type(arg_value)))
            logging.error('ClzRelationShips error: %s %s is invalid', arg_type, str(arg_value))

    def get_var(self, arg_type):
        if arg_type in DicArgvTypes.keys():
            return self.argvs.get(arg_type)
        else:
            import logging
            logging.error('ClzRelationShips error: %s cannot be found in argvs', arg_type)
            return None


