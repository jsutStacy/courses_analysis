import json


class StopWord(object):
    def __init__(self):
        self.words = self.assemble()

    def assemble(self):
        words = set(self.__load_stopwords('en'))
        words = words.union(set(self.__load_stopwords('et')))
        words = words.union(set(self.__get_teacher_names))
        words = sorted(list(words))
        return words

    @staticmethod
    def __load_stopwords(language):
        fname = 'stopwords_' + language + '.json'
        words = json.loads(open(fname).read())
        return words

    @staticmethod
    def __get_teacher_names():
        data = open('teachers.json').read()
        teachers = json.loads(data)

        names = []
        for teacher in teachers:
            for name in teacher['name'].split():
                names.append(name.lower())

        return names


if __name__ == '__main__':
    sw = StopWord()
    print sw.words