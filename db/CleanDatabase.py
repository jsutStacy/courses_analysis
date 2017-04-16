from db.DataModel import db, Course, Lecture
from utils.SemesterUtils import parse_semesters
import os
import sys


def is_valid_semester(course_entry, allowed):
    return any([x[0] == course_entry.year and x[1] == course_entry.semester for x in allowed])

if __name__ == '__main__':
    prefix = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

    lectures = Lecture.select().where(Lecture.time.is_null(True))
    for lec in lectures:
        path = prefix + lec.path
        if lec.path and os.path.exists(path):
            os.remove(path)

    semesters = []
    if len(sys.argv) == 2:
        semesters = parse_semesters(sys.argv[1])
        courses = Course.select()
        with db.atomic():
            for lec in lectures:
                lec.delete_instance()
            for course in courses:
                if is_valid_semester(course, semesters):
                    continue
                course.delete_instance(recursive=True)
