from nltk import WordNetLemmatizer
from nltk import word_tokenize
from db.DataModel import db, Course, Lecture, LectureWord, CourseWord, CorpusWord
from StopWord import StopWord
from pyvabamorf import analyze
from langdetect import detect
import pathos.multiprocessing as mp
import sys


class Tokenizer(object):
    def __init__(self):
        self.debug = False
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = StopWord().words

        thread_count = 7
        if len(sys.argv) == 2:
            thread_count = int(sys.argv[0])
        self.pool = mp.ThreadingPool(thread_count)

    def __extract_lecture_tokens(self, lecture):
        print "Course {} Lecture: {}".format(lecture.course.id, lecture.id)

        text = lecture.content
        try:
            tokens = word_tokenize(text)
        except UnicodeEncodeError:
            tokens = []

        if not tokens:
            return []

        est_text = self.__is_estonian(text)

        token_dict = {}
        for token in tokens:
            token = token.lower()

            # check if string consists of alphabetic characters only
            if not (token.isalpha() and len(token) > 2):
                continue

            try:
                if est_text:
                    lem_word = analyze(token)[0]['analysis'][0]['lemma']
                else:
                    lem_word = self.lemmatizer.lemmatize(token)
            except Exception:
                lem_word = token

            if lem_word not in self.stopwords:
                if self.debug:
                    print "{}: {}".format(token.encode('utf-8'), lem_word.encode('utf-8'))
                if lem_word in token_dict:
                    token_dict[lem_word] += 1
                else:
                    token_dict[lem_word] = 1

        return self.__compose_lecture_rows(lecture, token_dict)

    @staticmethod
    def __is_estonian(text):
        est = False
        try:
            est = detect(text) == 'et'
        except Exception:
            pass
        return est

    @staticmethod
    def __get_lectures(course):
        lectures = Lecture.select().where(Lecture.course == course)
        return list(lectures)

    @staticmethod
    def __get_courses(course_id=0):
        if course_id:
            courses = Course.select().where(Course.id == course_id)
        else:
            courses = Course.select()
        return list(courses)

    def extract_all_lectures_tokens(self):
        result_lectures = self.pool.map(self.__extract_lecture_tokens, Lecture.select().where(Lecture.id < 50))

        with db.atomic():
            LectureWord.insert_many([x for y in result_lectures for x in y]).execute()

    @staticmethod
    def __compose_lecture_rows(lecture, token_dict):
        rows = []

        for token in token_dict:
            row_dict = {'lecture': lecture,
                        'word': token,
                        'count': token_dict[token],
                        'active': True,
                        'weight': 0}
            rows.append(row_dict)

        return rows

    @staticmethod
    def __get_lecture_words(lecture):
        lecture_words = list(LectureWord.select().where(LectureWord.lecture == lecture))
        return lecture_words

    def create_all_course_tokens(self):
        result_courses = self.pool.map(self.__create_course_tokens, self.__get_courses())

        with db.atomic():
            CourseWord.insert_many([x for y in result_courses for x in y]).execute()

    def __create_course_tokens(self, course):
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

        return self.__compose_course_rows(course, token_dict, lecture_token)

    @staticmethod
    def __compose_course_rows(course, token_dict, lecture_token):
        rows = []

        for token in token_dict:
            row_dict = {'course': course,
                        'word': token,
                        'count': token_dict[token],
                        'active': True,
                        'lectures': lecture_token[token]}
            rows.append(row_dict)

        return rows

    def create_corpus_tokens(self):
        token_dict = {}
        for course_word in CourseWord.select():
            if course_word.word in token_dict:
                token_dict[course_word.word] += course_word.count
            else:
                token_dict[course_word.word] = course_word.count

        result_corpus = self.pool.map(self.__compose_corpus_rows, token_dict.items())

        with db.atomic():
            CorpusWord.insert_many(result_corpus).execute()

    @staticmethod
    def __compose_corpus_rows(token):
        return {'word': token[0],
                'count': token[1],
                'active': True}

if __name__ == '__main__':
    tok = Tokenizer()
    # tok.debug = True

    # Download first time
    # from nltk import download
    #download('punkt')

    print "Extracting all lecture tokens"
    tok.extract_all_lectures_tokens()

    print "Creating course tokens"
    tok.create_all_course_tokens()

    print "Creating corpus tokens"
    tok.create_corpus_tokens()
