from sklearn.feature_extraction.text import CountVectorizer
import numpy as np


class CoOccurrence(object):

    def __init__(self, ngram_range=(2, 3), limit = 40):
        """
        E.g ngram_range(2,3) specifies that we are only interested in n-grams of size 2 and 3.
        Method find_co_occurring_words will return all n-grams that occur more times than the limit
        """
        self.count_model = CountVectorizer(ngram_range=ngram_range)
        self.limit = limit

    def find_co_occurring_words(self, corpus):
        co_occurrences = self.count_model.fit_transform(corpus)
        sum_occ = co_occurrences.sum(axis=0)

        co_occurring_words = [i for i, j in zip(self.count_model.get_feature_names(),
                              np.array(sum_occ)[0].tolist()) if j > self.limit]

        return self.__clean(co_occurring_words)

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
        :return: True if given word is a sub-ngram
        """
        return any(word in x for x in words)

    @staticmethod
    def __is_dup(co_word):
        """
        :param co_word:
        :return: True if at least two of the co-occurring words are the same
        """
        return any(co_word.count(word) > 1 for word in co_word.split(' '))
