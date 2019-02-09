import peewee
import os

DB_DIR = os.path.dirname(os.path.abspath('db/DataModel'))
db_name = DB_DIR + '/courses.sqlite'
db = peewee.SqliteDatabase(db_name)

class BaseModel(peewee.Model):
    class Meta:
        database = db


class Course(BaseModel):
    name = peewee.CharField()
    code = peewee.CharField()
    year = peewee.CharField()
    semester = peewee.CharField()
    url = peewee.CharField()
    path = peewee.CharField()


class Lecture(BaseModel):
    course = peewee.ForeignKeyField(Course)
    url = peewee.CharField()
    path = peewee.CharField()
    name = peewee.CharField()
    content = peewee.TextField()
    time = peewee.DateTimeField(null=True)
    size = peewee.DoubleField()


main_tables = [Course, Lecture]
db.create_tables(main_tables)

prefix = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

lectures = Lecture.select().where(Lecture.time.is_null(True))
print "lectures: {}".format(len(lectures))
for lec in lectures:
    path = prefix + lec.path
    if lec.path and os.path.exists(path):
        os.remove(path)

courses = Course.select()
print "courses: {}".format(len(courses))
with db.atomic():
    for lec in lectures:
        lec.delete_instance()
    for course in courses:
        course.delete_instance(recursive=True)



print "Courses: {}".format(len(Course.select()))
for c in Course.select():
    c.delete_instance()
        
print "Courses: {}".format(len(Course.select()))
print "Lectures: {}".format(len(Lecture.select()))
	
for l in Lecture.select():
    l.delete_instance()

print "Lectures: {}".format(len(Lecture.select()))
