from db.DataModel import Lecture, db
import pathos.multiprocessing as mp
import peewee
import docx
import os


class Docx2txt(object):
    def __init__(self, prefix, process_count=1):
        self.prefix = prefix
        self.pool = mp.ProcessingPool(process_count)

    def __convert(self, lecture):
        path = self.prefix+lecture.path
        if not os.path.exists(path):
            print "File not found: {0}".format(path)
            return
        try:
            doc = docx.Document(path)
            print lecture.url

            lecture.content = '\n'.join([p.text for p in doc.paragraphs])
        except Exception as e:
            print "Skipping due to ", e

        return lecture

    def extract_text(self):
        lectures = Lecture.select().where(Lecture.content == '', Lecture.url % "*docx")

        result_lectures = self.pool.map(self.__convert, lectures)

        for lecture in result_lectures:
            if lecture:
                try:
                    with db.transaction():
                        lecture.save()
                except peewee.OperationalError as e:
                    print e