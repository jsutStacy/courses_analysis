# -*- coding: utf-8 -*-

from db.DataModel import Lecture, db
import peewee
from bs4 import BeautifulSoup
import pathos.multiprocessing as mp


class Html2txt(object):
    def __init__(self, process_count=1):
        self.pool = mp.ProcessingPool(process_count)
        self.blacklist = \
            [u'Lahenduste esitamiseks peate olema sisse loginud ja kursusele registreerunud.',
             u'Antud kursusel pole ühtegi ülesannet.',
             u'Sellele ülesandele ei saa hetkel lahendusi esitada.',
             u'You must be logged in and registered to the course in order to submit solutions.',
             u'There are no tasks for this course.',
             u'Solutions to this task cannot be submitted at the moment.'
             ]

    def __convert(self, lecture):
        soup = BeautifulSoup(lecture.content, "lxml")
        for tag in soup.find_all(name='div', attrs={'class': 'alert'}):
            if any(sentence in tag.get_text() for sentence in self.blacklist):
                tag.decompose()
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