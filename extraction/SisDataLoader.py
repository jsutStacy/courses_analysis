import csv
import sys
import os.path
import datetime

from db.DataModel import Lecture, Course, db
from utils.SemesterUtils import parse_semesters
from utils.ConfigReader import Config


class LectureKey(object):
    def __init__(self, code, year, semester):
        self.code = code
        self.year = year
        self.semester = semester

    def __hash__(self):
        return hash((self.code, self.year, self.semester))

    def __eq__(self, other):
        return (self.code, self.year, self.semester) == (other.code, other.year, other.semester)

    def __ne__(self, other):
        return not(self == other)

    def __str__(self):
        return self.code + '-' + self.year + '-' + self.semester


class SisDataLoader(object):

    def __init__(self, filename, allowed_semesters):
        self.filename = filename
        self.col_names = {}

        if allowed_semesters:
            self.allowed_semesters = allowed_semesters
        else:
            self.allowed_semesters = Config().get_allowed_semesters()

    def read_csv(self):
        result = {}
        with open(self.filename, 'rb') as csv_file:
            reader = csv.reader(csv_file, delimiter='\t', quotechar='|')
            header_done = False
            for row in reader:
                if not header_done:
                    self.col_names = self.__determine_columns(row)
                    print self.col_names
                    header_done = True
                    continue

                if int(row[self.col_names['KL_KEEL']]) != 2 \
                        or row[self.col_names['WWW']] == 'NULL':  # Include only 'english' based entries with proper WWW
                    continue

                semester = self.__determine_semester(row[self.col_names['WWW']])
                if semester and self.__is_semester_allowed(row[self.col_names['KL_OPPEAASTA']], semester):
                    key = self.__create_key(row, semester)
                    if key in result:
                        result[key] = result[key] + '\n' + row[self.col_names['KIRJELDUS']]
                    else:
                        result[key] = self.__compose_content(row)

        print result
        self.__persist(result)

    def __is_semester_allowed(self, year, semester):
        if not self.allowed_semesters:  # In case empty, allow everything
            return True

        for x in self.allowed_semesters:
            if x[0] == year and x[1] == semester:
                return True
        return False

    def __create_key(self, row, semester):
        return LectureKey(row[self.col_names['AINEKOOD']], row[self.col_names['KL_OPPEAASTA']], semester)

    def __compose_content(self, row):
        content = []
        if not row[self.col_names['OPIEESMARK']] == 'NULL':
            content.append(row[self.col_names['OPIEESMARK']])

        if not row[self.col_names['YLDEESMARK']] == 'NULL':
            content.append(row[self.col_names['YLDEESMARK']])

        if not row[self.col_names['KIRJELDUS']] == 'NULL':
            content.append(row[self.col_names['KIRJELDUS']])

        return '\n'.join(content)

    def __persist(self, results):
        rows = []
        for k, v in results.items():
            course = Course.select().where(Course.code == k.code, Course.year == k.year, Course.semester == k.semester)
            if not course.exists():
                print "Non-existing course in SIS data: {}".format(k)
                continue

            rows.append({'course': course,
                        'url': '',
                        'path': self.filename,
                        'name': 'SISdata',
                        'content': v.decode('latin-1').encode('utf-8'),
                        'time': datetime.datetime.now(),
                        'size': 0
                         })

        with db.atomic():
            Lecture.insert_many(rows).execute()

    @staticmethod
    def __determine_semester(www):
        semester = ''
        if 'spring' in www:
            semester = 'spring'
        elif 'fall' in www:
            semester = 'fall'
        return semester

    @staticmethod
    def __determine_columns(header_row):
        columns = {}

        idx = 0
        for column in header_row:
            if not column:
                continue
            columns[column] = idx
            idx += 1
        return columns

if __name__ == '__main__':
    semesters = []
    if len(sys.argv) == 2:
        semesters = parse_semesters(sys.argv[1])

    prefix = os.path.dirname(os.path.abspath(__file__))
    SisDataLoader(prefix + '/sis_data.csv', semesters).read_csv()