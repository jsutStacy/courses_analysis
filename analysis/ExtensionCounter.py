"""
The script at hand was created with the purpose of finding out what
possible extensions can be mined and how many of them actually are.
"""

from db.DataModel import Lecture
import operator


class ExtensionCounter(object):

    def __init__(self):
        self.blacklist = ['be', 'html']

    def print_all_extensions(self):
        extensions = sorted(self.__count_ext().items(), key=operator.itemgetter(1), reverse=True)
        for k, v in extensions:
            print k, v

    def __count_ext(self):
        extensions = {}
        lectures = Lecture.select().where(Lecture.content == '')
        for lecture in lectures:
            clean_url = None
            if lecture.url.startswith('https'):
                clean_url = lecture.url[8:]
            elif lecture.url.startswith('http'):
                clean_url = lecture.url[7:]

            ext = lecture.name.split('.')[-1]
            if ext in self.blacklist \
                    or (not ext.isalpha()) \
                    or (not clean_url)  \
                    or clean_url.find('/') < 0\
                    or ext.strip() == '' \
                    or lecture.name.find('.') < 0:
                continue

            if ext in extensions:
                extensions[ext] += 1
            else:
                extensions[ext] = 1
        return {k: v for k, v in extensions.iteritems() if v > 1 and len(k) < 5}

if __name__ == '__main__':
    ExtensionCounter().print_all_extensions()