from pylatexenc.latex2text import LatexNodes2Text
from db.DataModel import Lecture, db
import pathos.multiprocessing as mp
import peewee
import os


class Tex2txt(object):
    def __init__(self, prefix, process_count=1):
        self.prefix = prefix
        self.pool = mp.ProcessingPool(process_count)

    def __convert(self, lecture):
        path = self.prefix+lecture.path
        if not os.path.exists(path):
            print "File not found: {}".format(path)
            return
        try:
            with open(path, 'r') as f:
                lecture.content = LatexNodes2Text().latex_to_text(f.read())
            print lecture.url
        except Exception as e:
            print "Skipping due to {}".format(e)

        return lecture

    def extract_text(self):
        lectures = Lecture.select().where(Lecture.content == '', Lecture.url % "*tex")

        result_lectures = self.pool.map(self.__convert, lectures)

        for lecture in result_lectures:
            if lecture:
                try:
                    with db.transaction():
                        lecture.save()
                except peewee.OperationalError as e:
                    print e
