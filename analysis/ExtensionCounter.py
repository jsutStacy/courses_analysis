"""
The script at hand was created with the purpose of finding out what
possible extensions can be mined and how many of them actually are.
"""

from db.DataModel import Lecture
import operator


class ExtensionCounter(object):

    def print_all_extensions(self):
        extensions = sorted(self.__count_ext().items(), key=operator.itemgetter(1), reverse=True)
        for k, v in extensions:
            print k, v

    @staticmethod
    def __count_ext():
        extensions = {}
        lectures = Lecture.select()
        for lecture in lectures:
            if lecture.path == "html2txt":
                continue
            ext = lecture.name.split('.')[-1]
            if ext in extensions:
                extensions[ext] += 1
            else:
                extensions[ext] = 1
        return extensions

if __name__ == '__main__':
    ExtensionCounter().print_all_extensions()