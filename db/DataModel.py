import peewee
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
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


class LectureWord(BaseModel):
    lecture = peewee.ForeignKeyField(Lecture)
    word = peewee.CharField()
    count = peewee.IntegerField()
    weight = peewee.DoubleField()


class CourseWord(BaseModel):
    course = peewee.ForeignKeyField(Course)
    word = peewee.CharField()
    count = peewee.IntegerField()


class CorpusWord(BaseModel):
    word = peewee.CharField()
    count = peewee.IntegerField()


class TopicWord(BaseModel):
    topic = peewee.IntegerField()
    word = peewee.CharField()
    weight = peewee.DoubleField()


class CourseTopic(BaseModel):
    course = peewee.ForeignKeyField(Course)
    topic = peewee.IntegerField()
    weight = peewee.DoubleField()


class CourseTopicInfo(BaseModel):
    topic = peewee.IntegerField()
    name = peewee.CharField()


class LDALogLikelihood(BaseModel):
    iteration = peewee.IntegerField()
    loglikelihood = peewee.DoubleField()


class LectureTopic(BaseModel):
    lecture = peewee.ForeignKeyField(Lecture)
    topic = peewee.IntegerField()
    weight = peewee.DoubleField()


class LectureTopicWord(BaseModel):
    topic = peewee.IntegerField()
    course = peewee.ForeignKeyField(Course)
    word = peewee.CharField()
    weight = peewee.DoubleField()


class MaterialTopicWord(BaseModel):
    topic = peewee.IntegerField()
    word = peewee.CharField()
    weight = peewee.DoubleField()


class MaterialTopic(BaseModel):
    lecture = peewee.ForeignKeyField(Lecture)
    topic = peewee.IntegerField()
    weight = peewee.DoubleField()


class MaterialTopicInfo(BaseModel):
    topic = peewee.IntegerField()
    name = peewee.CharField()


if __name__ == '__main__':
    support_tables = [CourseWord, LectureWord, CorpusWord, TopicWord, CourseTopic, LDALogLikelihood,
                      LectureTopic, LectureTopicWord, CourseTopicInfo, MaterialTopic, MaterialTopicWord,
                      MaterialTopicInfo]
    main_tables = [Course, Lecture]
    if 'lecture' in db.get_tables():
        with db.atomic():
            for table in support_tables:
                table.delete().execute()
            Lecture.update(time=None).execute()
    else:
        db.create_tables(main_tables, safe=True)
        db.create_tables(support_tables, safe=True)
