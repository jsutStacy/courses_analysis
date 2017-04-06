import json
import os.path


class StopWord(object):
    def __init__(self):
        self.prefix = os.path.dirname(os.path.abspath(__file__))
        self.lang_words = set(self.__load_stopwords('et')).union(set(self.__load_stopwords('en')))
        self.teachers = set(self.__get_teacher_names())

    def get_all_stopwords(self):
        return self.lang_words.union(self.teachers)

    def get_lang_stopwords(self):
        return self.lang_words

    def __load_stopwords(self, language):
        filename = self.prefix + '/stopwords_' + language + '.json'
        words = json.loads(open(filename).read())
        return words

    def __get_teacher_names(self):
        path = self.prefix + '/teachers.json'

        names = []
        if os.path.exists(path):
            data = open(path).read()
            teachers = json.loads(data)
            for teacher in teachers:
                for name in teacher['name'].split():
                    names.append(name.lower())

        return names


if __name__ == '__main__':
    sw = StopWord()
    print sw.get_all_stopwords()