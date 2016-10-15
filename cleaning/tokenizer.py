from nltk import WordNetLemmatizer
from nltk import sent_tokenize, word_tokenize
from db.DataModel import db, Course, Lecture, LectureWord, CourseWord, CorpusWord
from StopWord import StopWord
from CleanWordTables import Cleaner
from CoOccurrence import CoOccurrence
from pyvabamorf import analyze
from langdetect import detect


class Tokenizer(object):
    def __init__(self):
        self.debug = False
        self.lemmatizer = WordNetLemmatizer()
        self.sw = StopWord()
        self.co_occ = CoOccurrence()
        self.co_occurring_words = []

    def __extract_lecture_tokens(self, lecture):
        print "Course {} Lecture: {}".format(lecture.course.id, lecture.id)
        text = lecture.content
        try:
            sentences = sent_tokenize(text)  # Split raw text to sentences
        except UnicodeEncodeError:
            sentences = []

        if not sentences:
            return None

        est_text = self.__is_estonian(text)  # Different lemmatizer should be applied in case of Estonian text

        token_dict = {}
        clean_sentences = []  # Keep track of sentences once they have been cleaned for co-occurrence
        for sentence in sentences:
            tokenized_sentence = word_tokenize(sentence)
            clean_sentence = []
            prev_word = ''
            for token in tokenized_sentence:
                token = token.lower()

                if prev_word:
                    token = prev_word + token
                    prev_word = ''

                if len(token) < 3:
                    continue

                # check if string consists of alphabetic characters only, don't include teacher names
                skip, prev_word = self.__is_alpha(token)
                if skip or any([token in w for w in self.sw.teachers]):
                    continue

                try:
                    if est_text:
                        lem_word = analyze(token)[0]['analysis'][0]['lemma']
                    else:
                        lem_word = self.lemmatizer.lemmatize(token)
                except Exception:
                    lem_word = token

                #Post-lemmatization length check
                if len(lem_word) < 3:
                    continue

                if lem_word not in self.sw.words:
                    clean_sentence.append(lem_word)
                    if self.debug:
                        print "{}: {}".format(token.encode('utf-8'), lem_word.encode('utf-8'))
                    if lem_word in token_dict:
                        token_dict[lem_word] += 1
                    else:
                        token_dict[lem_word] = 1
            clean_sentence.append('')  # Empty string, so that sentence would end with a space
            clean_sentences.append(' '.join(clean_sentence))

        return lecture, token_dict, clean_sentences

    @staticmethod
    def __is_alpha(token):
        if token.isalpha():
            return False, ''
        #Special handling of '-' case
        sym = [i for i, ltr in enumerate(token) if ltr == '-']
        if not sym or not token.replace('-', '').isalpha():
            return True, ''

        last = len(token)-1
        for idx in sym:
            if idx == 0:
                return True, ''
            if idx == last:
                return True, token[:-1]
        return False, ''

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
        result_data = [x for x in (self.__extract_lecture_tokens(lec) for lec in Lecture.select()) if x]

        # Perform co-occurrence over entire word corpus, filter by course code limit
        docs = [(y[0].course.code, y[2]) for y in result_data]
        self.co_occurring_words = self.co_occ.find_co_occurring_words(docs)
        print self.co_occurring_words
        # Re-count co-occurring words and remove 'standalone' words
        result_data = [self.__adjust_lecture_counts(res_data) for res_data in result_data]

        # Compose data set for mass insert
        persistent_tokens = [self.__compose_lecture_rows(entry) for entry in result_data]

        # One atomic bulk insert for faster performance
        with db.atomic():
            LectureWord.insert_many([x for y in persistent_tokens for x in y]).execute()

    def __adjust_lecture_counts(self, res_data):
        token_dict = res_data[1]
        clean_sentences = res_data[2]
        for word in self.co_occurring_words:
            contains = True
            for single_word in word.split(' '):
                if single_word in token_dict:  # Delete words that that make up co-occurring words
                    del token_dict[single_word]
                else:
                    contains = False

            #Dictionary has to contain individual words, skip if it doesn't
            if not contains:
                continue

            count = sum([x.count(''.join([word, ' '])) for x in clean_sentences])
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
        result_courses = [self.__create_course_tokens(course) for course in self.__get_courses()]

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

        __infrequent_words = [k for k, v in token_dict.items() if v < 3]
        for k in __infrequent_words:
            del token_dict[k]

        result_corpus = [self.__compose_corpus_rows(word) for word in token_dict.items()]

        with db.atomic():
            CorpusWord.insert_many(result_corpus).execute()

        return __infrequent_words

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
    infrequent_words = tok.create_corpus_tokens()

    # Remove infrequent words from other word tables
    cleaner = Cleaner()
    cleaner.clean_infrequent_words(infrequent_words)