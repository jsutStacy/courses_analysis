# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
from items import CoursesItem
from items import DataItem
import urllib
from db.DataModel import Course, Lecture, db
from scraping.settings import ALLOWED_EXTENSIONS
import peewee
import datetime


class CoursePipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, CoursesItem):
            course_code = ''.join(item['code'])
            year = item['year']
            semester = item['semester']

            #Check if entry already exists
            course = Course.select().where(Course.code == course_code, Course.year == year, Course.semester == semester)

            if not course.exists():
                print "course record not found, creating"
                with db.atomic():
                    try:
                        Course.create(
                            code=course_code,
                            name=''.join(item['title']),
                            year=item['year'],
                            semester=semester,
                            url=''.join(item['link']),
                            path='raw_data'.join(item['link'])
                        )
                    except peewee.OperationalError as e:
                        print "Could not create a record for {} due to {}".format(course_code, e)

        return item


class DataPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, DataItem):
            url = ''.join(item['link'])
            dir_name = 'raw_data' + ''.join(item['path']) + '/'
            course_code = ''.join(item['course_code'])
            content = ''.join(item['content'])
            path = ''
            year = ''.join(item['year'])
            semester = ''.join(item['semester'])
            prefix = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

            course = Course.select().where(Course.code == course_code, Course.year == year, Course.semester == semester)
            if not course.exists():
                print "Non-existing course: {}".format(course_code)
                return

            if len(content) == 0 and not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                except OSError as e:
                    print "Could not create directory: {} due to {}".format(dir_name, e)

            lecture = Lecture.select().where(Lecture.course == course, Lecture.url == url)
            file_size = 0
            # if no lecture record and no content, then download data (pdf, pptx, etc.) according to url
            if len(content) == 0:
                try:
                    info = urllib.urlopen(url).info()
                    if 'Content-Length' in info:
                        file_size = float(info['Content-Length'])
                except Exception as e:
                    print "Failed to retrieve file size for {} due to {}".format(url, e)
                if not lecture.exists():
                    path = self.__download(url, dir_name)
                else:
                    lecture_instance = lecture.first()

                    # Re-download only if the file has been updated
                    if lecture_instance.size == 0 or lecture_instance.size != file_size:
                        os.remove(prefix + lecture_instance.path)
                        self.__download(url, dir_name)

            if not lecture.exists():
                print "Lecture record not found, creating ..."
                title = self.__get_title(url)
                with db.atomic():
                    try:
                        Lecture.create(
                            course=course,
                            url=url,
                            path=path,
                            name=title,
                            content=content,
                            size=file_size,
                            time=datetime.datetime.now()
                        )
                    except peewee.OperationalError as e:
                        print "Could not create a record for course {} lecture {} due to {}".format(course_code, url, e)
            else:
                with db.atomic():
                    try:
                        lecture_instance = lecture.first()
                        lecture_instance.content = content
                        lecture_instance.time = datetime.datetime.now()
                        lecture_instance.save()
                    except peewee.OperationalError as e:
                        print e
        return item

    @staticmethod
    def __download(url, dir_name):
        filename = os.path.basename(url)
        path = dir_name + filename
        print "Saving {} => {}".format(url, path)
        try:
            urllib.urlretrieve(url, path)
        except IOError as e:
            print "Could not save file: {} into {}. Cause {}".format(url, path, e)
        return path

    @staticmethod
    def __get_title(url):
        title = url.split("/")
        return title[-1] if url.endswith(ALLOWED_EXTENSIONS) else "Web content - " + str(title[-1])