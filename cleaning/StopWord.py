import json
import os.path


class StopWord(object):
    def __init__(self):
        self.prefix = os.path.dirname(os.path.abspath(__file__))
        self.et_words = set(self.__load_stopwords('et'))
        self.en_words = set(self.__load_stopwords('en'))
        self.teachers = set(self.__get_teacher_names())

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
    print sw.et_words.union(sw.en_words)