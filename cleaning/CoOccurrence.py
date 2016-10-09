from sklearn.feature_extraction.text import CountVectorizer
import numpy as np


class CoOccurrence(object):

    def __init__(self, pool, ngram_range=(2, 3), word_limit = 15, id_limit=2):
        """
        E.g ngram_range(2,3) specifies that we are only interested in n-grams of size 2 and 3.

        word_limit specifies the minimum amount of times a co-occurring word should be present
        over entire corpus.

        id_limit specifies the minimum amount of unique group ids(e.g course id, lecture id)
        a co-occurring word should appear in.
        """
        self.count_model = CountVectorizer(ngram_range=ngram_range)
        self.limit = word_limit
        self.id_limit = id_limit
        self.pool = pool
        self.docs = []

    def find_co_occurring_words(self, docs):
        """
        :param docs: list of pairs with the first value being a unique id, second lecture sentences
        :return: a filtered list of n-grams
        """
        self.docs = docs

        corpus = [x for y in self.docs for x in y[1]]  # Flatten results
        co_occurrences = self.count_model.fit_transform(corpus)
        sum_occ = co_occurrences.sum(axis=0)

        co_occurring_words = [i for i, j in zip(self.count_model.get_feature_names(),
                              np.array(sum_occ)[0].tolist()) if j >= self.limit]

        cleaned_words = self.__clean(co_occurring_words)
        infrequent_words = self.pool.map(self.__is_infrequent, cleaned_words)

        return [x for x in cleaned_words if x not in infrequent_words]

    def __is_infrequent(self, word):
        """
        Filter co-occurring words by identifier(e.g course id) limit
        :param word:
        :return: provided word if it is infrequent, None otherwise
        """
        ids = set([unique_id for unique_id, lecture in self.docs if word in lecture])
        return word if len(ids) < self.id_limit else None

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
