from sklearn.feature_extraction.text import CountVectorizer
import numpy as np


class CoOccurrence(object):
    """
        E.g ngram_range(2,3) specifies that we are only interested in n-grams of size 2 and 3.
        Method find_co_occurring_words will return all n-grams that occur more times than the limit
    """
    def __init__(self, ngram_range=(2, 3), limit = 20):
        self.count_model = CountVectorizer(ngram_range=ngram_range)
        self.limit = limit

    def find_co_occurring_words(self, corpus):
        co_occurrences = self.count_model.fit_transform(corpus)
        sum_occ = co_occurrences.sum(axis=0)

        return [i for i, j in zip(self.count_model.get_feature_names(), np.array(sum_occ)[0].tolist()) if j > self.limit]
