"""Script for removing words from all the 'word'-related DB tables"""

from StopWord import StopWord
from db.DataModel import db, CourseWord, LectureWord, CorpusWord
import peewee


class Cleaner(object):

    def clean_infrequent_words(self, infrequent_words=None):
        if not infrequent_words:
            infrequent_words = self.__get_infrequent_words()
            self.__clean_words_table(CorpusWord, infrequent_words)

        self.__clean_words_table(CourseWord, infrequent_words)
        self.__clean_words_table(LectureWord, infrequent_words)

    def clean_stopwords(self):
        stop_words = StopWord().get_all_stopwords()
        self.__clean_words_table(CourseWord, stop_words)
        self.__clean_words_table(LectureWord, stop_words)
        self.__clean_words_table(CorpusWord, stop_words)

    @staticmethod
    def __get_infrequent_words():
        corpus_words = CorpusWord.select().where(CorpusWord.count < 2)
        return [corpus.word for corpus in corpus_words]

    @staticmethod
    def __clean_words_table(table, removable_words):
        print "Cleaning table {}".format(table.__name__)

        current_records = [record for record in table.select() if record.word in removable_words]

        try:
            with db.transaction():
                for record in current_records:
                    record.delete_instance()
        except peewee.OperationalError as e:
            print e


if __name__ == '__main__':
    tok = Cleaner()
    tok.clean_stopwords()
    tok.clean_infrequent_words()