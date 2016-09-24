"""Script for removing stopwords from all the 'word'-related DB tables"""

from StopWord import StopWord
import peewee
from db.DataModel import db, CourseWord, LectureWord, CorpusWord


def main():
    stopwords = StopWord().words

    clean_words_table(CourseWord, stopwords)
    clean_words_table(LectureWord, stopwords)
    clean_words_table(CorpusWord, stopwords)


def clean_words_table(table, stopwords):
    words = table.select()
    words = [word for word in words if word.word in stopwords]

    for word in words:
        try:
            with db.transaction():
                word.delete_instance()
        except peewee.OperationalError as e:
            print e


if __name__ == '__main__':
    main()