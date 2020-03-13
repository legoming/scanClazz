# -*- coding: utf-8 -*-

class NameSpaceUtil(object):

    def __init__(self):
        self.stack = []

    def pushpop(self, data):
        """
        进栈\出栈函数
        """
        tmp = str(data).strip()
        if tmp is None or len(tmp) < 1:
            return
        if tmp.find(r'namespace ') >= 0 and \
           tmp.find(r'using namespace') < 0 and \
           tmp.find(r'}') < 0 and \
           tmp.find(r'=') < 0 and \
           not tmp.endswith(r';'):
            ns = tmp
            try:
                ns = tmp[:tmp.index(r'{') - 1]
            except:
                pass
            ns = ns.replace(r'namespace ', r'').strip()
            print('push namespace ' + ns + ' from \t\t' + str(data))
            self.stack.append(ns)
        elif tmp.find(r'{') >= 0:
            print('push {')
            self.stack.append(r'{')
        if tmp.find(r'}') >= 0:
            # print('pop ' + self.stack[-1])
            # print('pop before ' + str(self.stack))
            print('pop ' + self.stack[-1])
            self.stack.pop()

    def getNamespace(self):
        # print('try to getNamespace')
        # fixme， namespace not working untill 200313
        # return ''
        if len(self.stack) < 1:
            return ''
        # for i in range(-1, -len(self.stack), -1):
        #     if self.stack[i] != r'{':
        #         print('get namespace ' + self.stack[i])
        #         return self.stack[i];
        #     # print(str(i) + ' ' + self.stack[i])
        ns = ''
        for i in range(-1, -len(self.stack)-1, -1):
            if self.stack[i] != r'{':
                if ns == '':
                    ns = self.stack[i]
                else:
                    ns = self.stack[i] + '::' + ns
        #ns.replace(r'::', r'_')
        print('get namespace ' + ns)
        return ns

    def gettop(self):
        """
        取栈顶
        """
        return self.stack[-1]




