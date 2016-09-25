from nltk import WordNetLemmatizer
from nltk import sent_tokenize, word_tokenize
from db.DataModel import db, Course, Lecture, LectureWord, CourseWord, CorpusWord
from StopWord import StopWord
from CoOccurrence import CoOccurrence
from pyvabamorf import analyze
from langdetect import detect
import pathos.multiprocessing as mp
import sys


class Tokenizer(object):
    def __init__(self):
        self.debug = False
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = StopWord().words
        self.co_occ = CoOccurrence()
        self.co_occurring_words = []

        thread_count = 7
        if len(sys.argv) == 2:
            thread_count = int(sys.argv[1])
        self.pool = mp.ThreadingPool(thread_count)

    def __extract_lecture_tokens(self, lecture):
        print "Course {} Lecture: {}".format(lecture.course.id, lecture.id)
        text = lecture.content
        try:
            sentences = sent_tokenize(text)  # Split raw text to sentences
        except UnicodeEncodeError:
            sentences = []

        if not sentences:
            return [], {}, []

        est_text = self.__is_estonian(text)  # Different lemmatizer should be applied in case of Estonian text

        token_dict = {}
        clean_sentences = []  # Keep track of sentences once they have been cleaned for co-occurrence
        for sentence in sentences:
            tokenized_sentence = word_tokenize(sentence)
            clean_sentence = []
            for token in tokenized_sentence:
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
                    clean_sentence.append(lem_word)
                    if self.debug:
                        print "{}: {}".format(token.encode('utf-8'), lem_word.encode('utf-8'))
                    if lem_word in token_dict:
                        token_dict[lem_word] += 1
                    else:
                        token_dict[lem_word] = 1
            clean_sentences.append(' '.join(clean_sentence))

        return lecture, token_dict, clean_sentences

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
        # Tokenize and clean each lecture separately
        result_data = self.pool.map(self.__extract_lecture_tokens, Lecture.select())

        # Perform co-occurrence over entire word corpus
        corpus = [x for y in result_data for x in y[2]]  # Flatten results
        self.co_occurring_words = self.co_occ.find_co_occurring_words(corpus)

        # Re-count co-occurring words and remove 'standalone' words
        result_data = self.pool.map(self.__adjust_lecture_counts, result_data)

        # Compose data set for mass insert
        persistent_tokens = self.pool.map(self.__compose_lecture_rows, result_data)

        # One atomic bulk insert for faster performance
        with db.atomic():
            LectureWord.insert_many([x for y in persistent_tokens for x in y]).execute()

    def __adjust_lecture_counts(self, res_data):
        token_dict = res_data[1]
        clean_sentences = res_data[2]
        for word in self.co_occurring_words:
            for single_word in word.split(' '):
                if single_word in token_dict:  # Delete words that that make up co-occurring words
                    del token_dict[single_word]
            count = sum([x.count(word) for x in clean_sentences])
            if count > 0:
                token_dict[word] = count

        return res_data[0], token_dict

    @staticmethod
    def __compose_lecture_rows(lecture_row):
        rows = []
        token_dict = lecture_row[1]
        for token in token_dict:
            row_dict = {'lecture': lecture_row[0],
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
