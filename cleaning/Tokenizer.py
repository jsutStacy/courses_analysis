# coding: utf-8

from nltk import WordNetLemmatizer
from nltk import sent_tokenize, word_tokenize
from db.DataModel import db, Course, Lecture, LectureWord, CourseWord, CorpusWord
from StopWord import StopWord
from CoOccurrence import CoOccurrence
from langdetect import detect
from nltk import download, data, pos_tag
from estnltk import Text
import pathos.multiprocessing as mp
import unicodedata
import time
import datetime
import copy


class Tokenizer(object):
    def __init__(self):
        self.debug = False
        self.lemmatizer = WordNetLemmatizer()
        self.sw = StopWord()
        self.co_occ = CoOccurrence()
        self.co_occurring_words = []
        self.acronyms = {}
        self.latin_letters = {}
        self.detect_lang = detect
        self.tokenize_sent = sent_tokenize
        self.tokenize_word = word_tokenize
        self.tag_words = pos_tag
        self.est_analyser = Text
        self.ud = unicodedata
        self.pool = mp.ProcessingPool(8)

    def __extract_lecture_tokens(self, lecture):
        print "Course {} Lecture: {}".format(lecture.course.id, lecture.id)
        text = lecture.content
        try:
            sentences = self.tokenize_sent(text)  # Split raw text to sentences
        except UnicodeEncodeError:
            sentences = []

        if not sentences:
            return None

        est_text = self.__is_estonian(text)  # Different lemmatizer should be applied in case of Estonian text

        token_dict = {}
        clean_sentences = []  # Keep track of sentences once they have been cleaned for co-occurrence
        potential_acronyms = set()  # Words that could potentially be acronyms
        acronym_def = {}  # Words that are definitely acronyms, process as definitions
        for sentence in sentences:
            if est_text:  # In case of estonian text, lemmatize sentence immediately to take advantage of disambiguation
                est_processed_text = self.est_analyser(sentence.replace(chr(0), ''))  # VabaMorf will fail on ord(0)
                tokenized_sentence = est_processed_text.word_texts  # No lower case for tokenization
                tagged = est_processed_text.lemmas  # Just lemmatized words
            else:
                # No lower case for tokenization
                tokenized_sentence = self.tokenize_word(sentence)

                # POS tagged English words, not lemmatized, lower case
                tagged = self.tag_words([w.lower() for w in tokenized_sentence])

            clean_sentence = ['']
            prev_word = ''
            for i in range(len(tokenized_sentence)):
                token = tokenized_sentence[i].lower()

                if prev_word:
                    token = prev_word + token
                    prev_word = ''

                if len(token) < 3:
                    continue

                # check if string consists of alphabetic characters only, don't include teacher names
                skip, prev_word = self.__is_alpha(token)
                if skip or any([token in w for w in self.sw.teachers]):
                    continue

                lem_word = token
                acronym, definition = self.__resolve_potential_acronym(tokenized_sentence, i)
                if definition:
                    potential_acronyms.add(acronym)
                    acronym_def[acronym] = definition
                elif acronym:
                    potential_acronyms.add(acronym)
                else:  # Don't lemmatize acronyms
                    try:
                        if est_text:
                            if not '|' in tagged[i]:  # Choose the lemmatized version only when there was no conflict
                                lem_word = tagged[i].lower()  # Only correctly lemmatized words are lower-cased
                        else:
                            lem_word = self.lemmatizer.lemmatize(token, self.to_wordnet(tagged[i]))
                    except Exception as e:
                        print e

                #Post-lemmatization length check
                if len(lem_word) < 3:
                    continue

                if lem_word not in self.sw.lang_words:
                    clean_sentence.append(lem_word)
                    if self.debug:
                        print "{}: {}".format(token.encode('utf-8'), lem_word.encode('utf-8'))
                    if lem_word in token_dict:
                        token_dict[lem_word] += 1
                    else:
                        token_dict[lem_word] = 1
            if len(clean_sentence) > 1:
                clean_sentence.append('')  # Empty string, so that sentence would end with a space
                clean_sentences.append(' '.join(clean_sentence))

        return lecture, token_dict, clean_sentences, potential_acronyms, acronym_def

    def __is_latin(self, uchr):
        try:
            return self.latin_letters[uchr]
        except KeyError:
            return self.latin_letters.setdefault(uchr, 'LATIN' in self.ud.name(uchr, 'A'))

    def __is_alpha(self, token):
        if not self.__is_latin(token[0]):  # Skip foreign characters(e.g cyrillic)
            return True, ''

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
    def __resolve_potential_acronym(sentence, token_idx):
        w = sentence[token_idx]

        if len(w) > 4 or not (w.isupper() or (w[0].islower() and w[1:].isupper())
                              or (w[-1:].islower() and w[:-1].isupper())):
            return None, None

        #Not the first or the final word
        w = w.lower()
        sent_len = len(sentence)
        if sent_len == token_idx + 1:
            return w, None

        # Check if definition is in parenthesis
        next_w = sentence[token_idx+1]
        right_idx = token_idx + len(w) + 2
        if next_w == '(' and sent_len > right_idx and sentence[right_idx] == ')':  # Definition is in parenthesis
            definition = sentence[token_idx+2:right_idx]
            if all([True if definition[i][0].lower() == w[i] else False for i in range(len(definition))]):
                return w, ' '.join(definition).lower()

        # Check if acronym is in parenthesis
        left_idx = token_idx - (len(w)+1)
        if next == ')' and left_idx >= 0 and sentence[token_idx-1] == '(':
            definition = sentence[left_idx:token_idx-1]
            if all([True if definition[i][0].lower() == w[i] else False for i in range(len(definition))]):
                return w, ' '.join(definition).lower()
        return w, None

    @staticmethod
    def to_wordnet(tagged_word):
        w = tagged_word[0].lower()
        treebank_tag = tagged_word[1]
        if treebank_tag.startswith('J'):
            return 'a'
        elif treebank_tag.startswith('V') and not w.endswith('ing'):
            return 'v'
        elif treebank_tag.startswith('R'):
            return 'r'
        else:
            return 'n'

    def __is_estonian(self, text):
        est = False
        try:
            est = self.detect_lang(text) == 'et'
        except Exception as e:
            print e
        return est

    @staticmethod
    def __get_courses(course_id=0):
        if course_id:
            courses = Course.select().where(Course.id == course_id)
        else:
            courses = Course.select()
        return list(courses)

    def extract_all_lectures_tokens(self):
        # Tokenize and clean each lecture separately
        result_data = [x for x in (self.pool.map(self.__extract_lecture_tokens, Lecture.select())) if x]

        #Create acronym dictionary and replace acronyms with definitions
        self.__create_acronym_dict(result_data)
        result_data = self.pool.map(self.__replace_acronyms, result_data)

        # Perform co-occurrence over entire word corpus, filter by course code limit
        docs = [(y[0].course.code, y[2]) for y in result_data]
        self.co_occurring_words = self.co_occ.find_co_occurring_words(docs, self.acronyms)
        print "Co-occurring words:", self.co_occurring_words, "; total count:", len(self.co_occurring_words)
        # Re-count co-occurring words and remove 'standalone' words
        return self.pool.map(self.__adjust_lecture_counts, result_data)

    def persist_lecture_dict(self, lecture_data, rem_words):
        for w in rem_words:
            for lecture, lecture_dict in lecture_data:
                if w in lecture_dict:
                    del lecture_dict[w]

        # Compose data set for mass insert
        persistent_tokens = [self.__compose_lecture_rows(entry) for entry in lecture_data]

        # One atomic bulk insert for faster performance
        with db.atomic():
            LectureWord.insert_many([x for y in persistent_tokens for x in y]).execute()

    def __create_acronym_dict(self, res):
        for a, b, c, d, e in res:
            for k, v in e.iteritems():
                if k in self.acronyms and self.acronyms[k] != v:
                    self.acronyms[k] = k  # Conflict, don't change the acronym, use local dictionary instead
                else:
                    self.acronyms[k] = v
        print "Acronyms:", self.acronyms, "; total count:", len(self.acronyms)  # Global acronyms

    def __replace_acronyms(self, res):
        word_dict = res[1]
        potential_acronyms = res[3]
        local_def = res[4]
        for acronym in potential_acronyms:
            if acronym in word_dict:
                count = word_dict[acronym]
                if acronym in local_def:  # Legit acronym, replace it
                    del word_dict[acronym]
                    word_dict[local_def[acronym]] = count
                elif acronym in self.acronyms:  # Present in global acronym definition
                    del word_dict[acronym]
                    word_dict[self.acronyms[acronym]] = count

        return res[0], word_dict, res[2]  # lecture, dictionary, clean sentences

    def __adjust_lecture_counts(self, res_data):
        token_dict = res_data[1]
        clean_sentences = res_data[2]
        removable_words = set()
        for word in self.co_occurring_words:
            contains = True
            for single_word in word.split(' '):
                if single_word in token_dict:
                    removable_words.add(single_word)
                else:
                    contains = False

            #Dictionary has to contain individual words, skip counting if it doesn't
            if not contains:
                continue

            count = sum([x.count(' '.join(['', word, ''])) for x in clean_sentences])
            if count > 0:
                if word in token_dict:  # Could be an acronym
                    token_dict[word] += count
                else:
                    token_dict[word] = count

        # Delete words that that make up co-occurring words
        for w in removable_words:
            del token_dict[w]

        return res_data[0], token_dict

    @staticmethod
    def __compose_lecture_rows(lecture_row):
        rows = []
        token_dict = lecture_row[1]
        for token in token_dict:
            row_dict = {'lecture': lecture_row[0],
                        'word': token,
                        'count': token_dict[token],
                        'weight': 0}
            rows.append(row_dict)

        return rows

    @staticmethod
    def create_all_course_tokens(lecture_data):
        course_dicts = {}
        for lecture, lec_dict in lecture_data:
            course_id = lecture.course.id
            if course_id in course_dicts:
                info = course_dicts[course_id]
                for k, v in lec_dict.items():
                    if k in info[1]:
                        info[1][k] += lec_dict[k]  # word count
                    else:
                        info[1][k] = lec_dict[k]
            else:
                course_dicts[course_id] = [lecture.course, copy.deepcopy(lec_dict)]
        return course_dicts

    def persist_course_dict(self, courses_data, rem_words):
        for w in rem_words:
            for course_id, course_info in courses_data.items():
                if w in course_info[1]:
                    del course_info[1][w]

        result_courses = [self.__compose_course_rows(entry) for entry in courses_data.items()]

        with db.atomic():
            CourseWord.insert_many([x for y in result_courses for x in y]).execute()

    @staticmethod
    def __compose_course_rows(entry):
        rows = []
        course = entry[1][0]
        for word, word_info in entry[1][1].items():
            row_dict = {'course': course,
                        'word': word,
                        'count': word_info}  # remove
            rows.append(row_dict)
        return rows

    def create_corpus_tokens(self, courses_data):
        corpus_dict = {}

        for course_id, course_info in courses_data.items():
            course = course_info[0]
            course_dict = course_info[1]
            for word, count in course_dict.items():
                if word in corpus_dict:
                    corpus_dict[word][0] += count
                    corpus_dict[word][1].add(course.code)
                else:
                    word_courses = [course.code]
                    corpus_dict[word] = [count, set(word_courses)]

        rem_words = []
        for word, word_info in corpus_dict.items():
            count = word_info[0]
            courses_count = len(word_info[1])
            if count < 5 or courses_count < 3:
                rem_words.append(word)

        for word in rem_words:
            del corpus_dict[word]

        result_corpus = [self.__compose_corpus_rows(item) for item in corpus_dict.items()]

        with db.atomic():
            CorpusWord.insert_many(result_corpus).execute()

        return rem_words

    @staticmethod
    def __compose_corpus_rows(item):
        return {'word': item[0],
                'count': item[1][0]}


def measure_time(function, task_str, *args):
    start = time.clock()
    try:
        return function(*args)
    finally:
        print '{} in {}'.format(task_str, str(datetime.timedelta(seconds=time.clock()-start)))

if __name__ == '__main__':
    tok = Tokenizer()
    # tok.debug = True

    try:
        data.find('tokenizers/punkt')
    except LookupError:
        download('punkt')  # Download first time

    try:
        data.find('taggers/maxent_treebank_pos_tagger')
    except LookupError:
        download('maxent_treebank_pos_tagger')

    try:
        data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        download('averaged_perceptron_tagger')

    print "Extracting all lecture tokens"
    lec_data = measure_time(tok.extract_all_lectures_tokens, "Extracted lecture tokens")

    print "Creating course tokens"
    course_data = measure_time(tok.create_all_course_tokens, "Created course tokens", lec_data)

    print "Creating corpus tokens"
    removable = measure_time(tok.create_corpus_tokens, "Created corpus tokens", course_data)

    # Remove infrequent words and persist lecture and course words
    tok.persist_lecture_dict(lec_data, removable)
    tok.persist_course_dict(course_data, removable)
