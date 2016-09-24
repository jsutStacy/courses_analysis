from db.DataModel import Lecture, db
import peewee
from bs4 import BeautifulSoup
import pathos.multiprocessing as mp


class Html2txt(object):
    def __init__(self, process_count=1):
        self.pool = mp.ProcessingPool(process_count)

    @staticmethod
    def __convert(lecture):
        soup = BeautifulSoup(lecture.content)
        print lecture.url
        lecture.content = soup.get_text()
        lecture.path = 'html2txt'
        return lecture

    def extract_text(self):
        lectures = Lecture.select().where(Lecture.content != '', Lecture.path == "")

        result_lectures = self.pool.map(self.__convert, lectures)

        for lecture in result_lectures:
            if lecture:
                try:
                    with db.transaction():
                        lecture.save()
                except peewee.OperationalError as e:
                    print e