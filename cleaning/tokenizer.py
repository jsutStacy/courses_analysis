from nltk.stem import PorterStemmer
from nltk import WordNetLemmatizer
from nltk import word_tokenize
from db.DataModel import db, Course, Lecture, LectureWord, CourseWord, CorpusWord
import operator
import peewee
from StopWord import StopWord
from pyvabamorf import analyze
from langdetect import detect


class Tokenizer(object):
    def __init__(self, lemmatize=True):
        self.debug = False
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.lemmatize = lemmatize
        self.stopwords = self.__get_stopwords()

    @staticmethod
    def __get_stopwords():
        sw = StopWord()
        return set(sw.words)

    def lemstem(self, token):
        if self.lemmatize:
            return self.lemmatizer.lemmatize(token)
        else:
            return self.stemmer.stem(token)

    def extract_tokens(self, text):
        try:
            tokens = word_tokenize(text)
        except UnicodeEncodeError:
            tokens = []

        if not tokens:
            return {}

        est_text = self.__is_estonian(text)

        token_dict = {}
        for token in tokens:
            token = token.lower()

            # check if string consists of alphabetic characters only
            if not (token.isalpha() and len(token) > 2):
                continue

            try:
                if est_text:
                    lemstem_word = analyze(token)[0]['analysis'][0]['lemma']
                else:
                    lemstem_word = self.lemstem(token)
            except Exception:
                lemstem_word = token

            if lemstem_word not in self.stopwords:
                if self.debug:
                    print "{0}: {1}".format(token.encode('utf-8'), lemstem_word.encode('utf-8'))
                if lemstem_word in token_dict:
                    token_dict[lemstem_word] += 1
                else:
                    token_dict[lemstem_word] = 1

        return token_dict

    @staticmethod
    def __is_estonian(text):
        est = False
        try:
            est = detect(text) == 'et'
        except Exception:
            pass
        return est

    @staticmethod
    def __get_lecture_record(lecture_id):
        try:
            data = Lecture.select().where(Lecture.id == lecture_id).get()
            return data
        except Exception:
            return None

    def extract_lecture_tokens(self, lecture):
        if lecture is None:
            return False

        text = lecture.content
        tokens = self.extract_tokens(text)
        sorted_tokens = sorted(tokens.items(), key=operator.itemgetter(1))

        for token in sorted_tokens:
            try:
                with db.transaction() as txn:
                    LectureWord.create(
                        lecture=lecture,
                        word=token[0],
                        count=token[1],
                        active=True,
                        weight=0
                    )
                    txn.commit()
            except peewee.OperationalError as e:
                print "Could not create a record for lecture {0}, word {1}, {2}".format(lecture.id, token[0], e)

            if self.debug:
                print token

        return True

    @staticmethod
    def __get_course_record(course_id):
        try:
            data = Course.select().where(Course.id == course_id).get()
            return data
        except Exception:
            return None

    @staticmethod
    def __get_lectures(course):
        lectures = Lecture.select().where(Lecture.course == course)
        return list(lectures)

    def extract_course_tokens(self, lectures):
        print "Lecture count: {0}".format(len(lectures))
        for lecture in lectures:
            print "Lecture: {0}".format(lecture.id)
            self.extract_lecture_tokens(lecture)

    @staticmethod
    def __get_courses(course_id=0):
        if course_id:
            courses = Course.select().where(Course.id == course_id)
        else:
            courses = Course.select()
        return list(courses)

    def extract_all_course_tokens(self):
        for course in self.__get_courses():
            print course.id, course.name
            lectures = self.__get_lectures(course)
            self.extract_course_tokens(lectures)

    @staticmethod
    def __get_lecture_words(lecture):
        lecture_words = list(LectureWord.select().where(LectureWord.lecture == lecture))
        return lecture_words

    def create_course_tokens(self):
        for course in self.__get_courses():
            print "{}: {}".format(course.id, course.name.encode('utf8'))
            token_dict = {}
            lecture_token = {}

            for lecture in self.__get_lectures(course):
                lecture_words = self.__get_lecture_words(lecture)
                for lecture_word in lecture_words:
                    if not lecture_word.word in token_dict:
                        token_dict[lecture_word.word] = 0
                        lecture_token[lecture_word.word] = 0

                    token_dict[lecture_word.word] += lecture_word.count
                    lecture_token[lecture_word.word] += 1
            sorted_tokens = sorted(token_dict.items(), key=operator.itemgetter(1))
            for token in sorted_tokens:
                try:
                    with db.transaction() as txn:
                        CourseWord.create(
                            course=course,
                            word=token[0],
                            count=token[1],
                            active=True,
                            lectures=lecture_token[token[0]]
                        )
                        txn.commit()
                except peewee.OperationalError as e:
                    print "Could not create a record for course {0}, word {1}, {2}".format(course.name.encode('utf8'),
                                                                                           token[0].encode('utf8'), e)
    @staticmethod
    def __get_course_words(course_id=0):
        if course_id == 0:
            course_words = CourseWord.select()
        else:
            course_words = CourseWord.select().where(CourseWord.course == course_id)
        return list(course_words)

    def create_corpus_tokens(self):
        token_dict = {}
        for courseWord in self.__get_course_words():
            if courseWord.word in token_dict:
                token_dict[courseWord.word] += courseWord.count
            else:
                token_dict[courseWord.word] = courseWord.count

        sorted_tokens = sorted(token_dict.items(), key=operator.itemgetter(1))
        for token in sorted_tokens:
            print token
            try:
                with db.transaction() as txn:
                    CorpusWord.create(
                        word=token[0],
                        count=token[1],
                        active=True
                    )
                    txn.commit()
            except peewee.OperationalError as e:
                print "Could not create a record for word {}, {}".format(token[0], e)

    def calc_tf(self):
        for course in self.__get_courses(55):
            print course.name
            for lecture in self.__get_lectures(course):
                max_count = 0
                for lectureWord in self.__get_lecture_words(lecture):
                    max_count = max(max_count, lectureWord.count)

                for lectureWord in self.__get_lecture_words(lecture):
                    try:
                        with db.transaction():
                            lectureWord.weight = 0.5 + (0.5 * lectureWord.count) / max_count
                            lectureWord.save()
                    except peewee.OperationalError as e:
                        print e


if __name__ == '__main__':
    tok = Tokenizer()
    # tok.debug = True

    # Download first time
    # from nltk import download
    #download('punkt')

    print "Extracting all tokens"
    tok.extract_all_course_tokens()

    print "Creating course tokens"
    tok.create_course_tokens()

    # print "Calculating tf weights"
    # tok.calc_tf()

    tok.create_corpus_tokens()
