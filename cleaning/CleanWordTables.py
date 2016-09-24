"""Script for removing words from all the 'word'-related DB tables"""

from StopWord import StopWord
from db.DataModel import db, CourseWord, LectureWord, CorpusWord
import sys
import peewee


class Cleaner(object):
    def __init__(self, mode=2):
        self.remove_words = set(StopWord().words)
        if mode > 1:
            self.remove_words = self.remove_words.union(self.__get_infrequent_words())

    def clean(self):
        self.clean_words_table(CourseWord)
        self.clean_words_table(LectureWord)
        self.clean_words_table(CorpusWord)

    @staticmethod
    def __get_infrequent_words():
        corpus_words = CorpusWord.select().where(CorpusWord.count < 3)
        return [corpus.word for corpus in corpus_words]

    def clean_words_table(self, table):
        print "Cleaning table {}".format(table.__name__)

        current_records = [record for record in table.select() if record.word in self.remove_words]

        try:
            with db.transaction():
                for record in current_records:
                    record.delete_instance()
        except peewee.OperationalError as e:
            print e


if __name__ == '__main__':
    arg = 2
    if len(sys.argv) == 2 and len(sys.argv[1]) == 1:
        arg = int(sys.argv[1])

    tok = Cleaner(arg)
    tok.clean()