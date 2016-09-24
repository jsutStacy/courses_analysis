import json
import os.path


class StopWord(object):
    def __init__(self):
        self.prefix = os.path.dirname(os.path.abspath(__file__))
        self.words = self.assemble()

    def assemble(self):
        words = set(self.__load_stopwords('en'))
        words = words.union(set(self.__load_stopwords('et')))
        words = words.union(set(self.__get_teacher_names()))
        return words

    def __load_stopwords(self, language):
        filename = self.prefix + '\\stopwords_' + language + '.json'
        words = json.loads(open(filename).read())
        return words

    def __get_teacher_names(self):
        data = open(self.prefix + '\\teachers.json').read()
        teachers = json.loads(data)

        names = []
        for teacher in teachers:
            for name in teacher['name'].split():
                names.append(name.lower())

        return names


if __name__ == '__main__':
    sw = StopWord()
    print sw.words