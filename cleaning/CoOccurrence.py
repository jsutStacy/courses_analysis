from sklearn.feature_extraction.text import CountVectorizer
import numpy as np


class CoOccurrence(object):

    def __init__(self, ngram_range=(2, 4), word_limit = 20, id_limit=3):
        """
        E.g ngram_range(2,4) specifies that we are only interested in n-grams of size 2 and 4.

        word_limit specifies the minimum amount of times a co-occurring word should be present
        over entire corpus.

        id_limit specifies the minimum amount of unique group ids(e.g course id, lecture id)
        a co-occurring word should appear in.
        """
        self.count_model = CountVectorizer(stop_words=[''], lowercase=False,
                                           tokenizer=lambda text: text.split(' '), ngram_range=ngram_range)
        self.limit = word_limit
        self.id_limit = id_limit

    def find_co_occurring_words(self, docs, acronyms):
        """
        :param docs: list of pairs with the first value being a unique id, second lecture sentences
        :param acronyms: list of all acronyms
        :return: a filtered list of n-grams
        """

        all_co_occurrences = {}
        for doc in docs:
            if not doc[1] or (len(doc[1]) == 1 and doc[1][0].count(' ') < 3):
                continue

            co_occurrences = self.count_model.fit_transform(doc[1])
            sum_occ = co_occurrences.sum(axis=0)
            for i, j in zip(self.count_model.get_feature_names(), np.array(sum_occ)[0].tolist()):
                if i in all_co_occurrences:
                    all_co_occurrences[i][0] += j
                    all_co_occurrences[i][1].add(doc[0])
                else:
                    idx = [doc[0]]
                    all_co_occurrences[i] = [j, set(idx)]

        return self.__clean([k for k, v in all_co_occurrences.items()
                             if (v[0] >= self.limit and len(v[1]) >= self.id_limit) or k in acronyms])

    def __clean(self, words):
        """
        Sorts the co-occurring words according to n-gram size and processes each word
        :param words: co-occurring words to be clean
        :return: cleaned list of co-occurring words
        """
        words = sorted(words, cmp=lambda x, y: 1 if len(x.split(' ')) < len(y.split(' ')) else -1)
        res = []
        while words:
            word = words.pop()
            if not (self.__is_dup(word) or self.__is_sub_ngram(word, words)):
                res.append(word)
        return res

    @staticmethod
    def __is_sub_ngram(word, words):
        """
        :param word: to check against a list of words
        :param words: list of words to check
        :return: True if given word is a sub n-gram
        """
        return any(word in x for x in words)

    @staticmethod
    def __is_dup(co_word):
        """
        :param co_word:
        :return: True if at least two of the co-occurring words are the same(e.g 'num num')
        """
        return any(co_word.count(word) > 1 for word in co_word.split(' '))
