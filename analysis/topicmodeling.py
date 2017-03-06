import numpy as np
import lda
import lda.datasets
from sklearn.feature_extraction import DictVectorizer
from db.DataModel import Course, Lecture, CourseWord, LectureWord, LectureTopic, LectureTopicWord, \
    MaterialTopic, MaterialTopicWord
from db.DataModel import db, TopicWord, CourseTopic, LDALogLikelihood
import pathos.multiprocessing as mp
from TopicNameResolver2 import TopicNameResolver2


class TopicModeling(object):
    def __init__(self):
        self.debug = False
        self.n_top_words = 10  # Number of top words per topic to be persisted
        self.n_top_topic = 5  # Number of top topics per course to be persisted
        self.pool = mp.ProcessingPool(8)
        self.numpy = np

    def lda_over_lectures(self):
        """
        Peform LDA over lectures within the scope of an individual course.
        Basically we perform as many LDA modellings as there are courses.
        """

        lectures = []
        for course in Course.select():
            course_lectures = list(Lecture.select().where(Lecture.course == course))
            lda_tools = [DictVectorizer(), lda.LDA(n_topics=len(course_lectures), n_iter=1000, random_state=1)]
            lectures.append((course, course_lectures, LectureWord, lda_tools))

        res = self.pool.map(self.__lda_for_course_material, lectures)

        with db.atomic():
            LectureTopicWord.insert_many([x for y in res for x in y[0]]).execute()
            LectureTopic.insert_many([x for y in res for x in y[1]]).execute()

    def __lda_for_course_material(self, lecture_data):
        print "LDA for course: {}".format(lecture_data[0].name.encode('utf-8'))

        lectures = lecture_data[1]
        lectures_size = len(lectures)
        lecture_dict = []
        for lecture in lectures:
            lecture_words = lecture_data[2].select().where(lecture_data[2].lecture == lecture)
            lecture_dict.append(dict([(x.word, x.count) for x in lecture_words]))

        #Skip if there are no words in any of the dictionaries
        if all([False if d else True for d in lecture_dict]):
            return [], []

        lda_tools = lecture_data[3]
        model, vocab = self.__perform_lda(lecture_dict, lda_tools[0], lda_tools[1])

        lec_topic_words_rows = []
        for i, topic_dist in enumerate(model.topic_word_):
            top_topic_words = self.numpy.array(vocab)[self.numpy.argsort(topic_dist)][:-self.n_top_words - 1:-1]
            top_word_probs = topic_dist[self.numpy.argsort(topic_dist)][:-self.n_top_words - 1:-1]

            for top_word, top_weight in zip(top_topic_words, top_word_probs):
                row_dict = {'course': lecture_data[0],
                            'topic': i,
                            'word': top_word,
                            'weight': round(top_weight * 100, 2)}
                lec_topic_words_rows.append(row_dict)

            if self.debug:
                top_word_str = ", ".join([x.encode('utf-8') + "(" + str(round(y, 2) * 100) + "%)"
                                          for x, y in zip(top_topic_words, top_word_probs)])
                print('Topic {}: {}'.format(i, top_word_str))

        # Document-topic distributions
        doc_topic = model.doc_topic_
        lec_topic_rows = []
        for i in range(lectures_size):
            top_topics = self.numpy.argsort(doc_topic[i])[:-self.n_top_topic - 1:-1]
            topic_probs = doc_topic[i][top_topics]

            for top_topic, top_weight in zip(top_topics, topic_probs):
                row_dict = {'lecture': lectures[i],
                            'topic': top_topic,
                            'weight': round(top_weight * 100, 2)}
                lec_topic_rows.append(row_dict)

            if self.debug:
                title = lectures[i].path.split("/")[-1].encode('utf-8')
                doc_topic_str = ", ".join(
                    [str(x) + "(" + str(round(y * 100, 2)) + "%)" for x, y in zip(top_topics, topic_probs)])
                print("{} (top {} topics: {})".format(title, self.n_top_topic, doc_topic_str))

        return lec_topic_words_rows, lec_topic_rows

    def lda_over_all_material(self):
        """
        Perform LDA over all material without any course limitations. The topic count is 1/10 of the material count.
        """

        lectures = Lecture.select()
        lectures_dict = []
        for lecture in lectures:
            lecture_words = LectureWord.select().where(LectureWord.lecture == lecture)
            lectures_dict.append(dict([(x.word, x.count) for x in lecture_words]))

        topic_count = int(len(lectures_dict) / 10)

        print "Performing LDA over all material.."
        model, vocab = self.__perform_lda_default(lectures_dict, topic_count)

        topic_word_rows = []
        # Iterate over topic word distributions
        for i, topic_dist in enumerate(model.topic_word_):
            top_topic_words = np.array(vocab)[self.__max_values(topic_dist, self.n_top_words)]
            top_word_probs = topic_dist[np.argsort(topic_dist)][:-self.n_top_words - 1:-1]

            for top_word, top_weight in zip(top_topic_words, top_word_probs):
                row_dict = {'topic': i,
                            'word': top_word,
                            'weight': round(top_weight * 100, 2)}
                topic_word_rows.append(row_dict)

            if self.debug:
                top_word_str = ", ".join([x.encode('utf-8') + "(" + str(round(y * 100, 2)) + "%)"
                                         for x, y in zip(top_topic_words, top_word_probs)])
                print('Topic {}: {}'.format(i, top_word_str))

        # Document-topic distributions
        doc_topic = model.doc_topic_
        lecture_topic_rows = []
        for i in range(lectures.count()):
            top_topics = np.argsort(doc_topic[i])[:-self.n_top_topic - 1:-1]
            topic_probs = doc_topic[i][top_topics]

            for top_topic, top_weight in zip(top_topics, topic_probs):
                rounded_weight = round(top_weight * 100, 2)
                if rounded_weight < 10:
                    continue
                row_dict = {'lecture': lectures[i],
                            'topic': top_topic,
                            'weight': rounded_weight}
                lecture_topic_rows.append(row_dict)

            if self.debug:
                doc_topic_str = ", ".join(
                    [str(x) + "(" + str(round(y * 100, 2)) + "%)" for x, y in zip(top_topics, topic_probs)])
                print("{} (top {} topics: {})".format(lectures[i].name.encode('utf-8'),
                                                      self.n_top_topic, doc_topic_str))

        with db.atomic():
            MaterialTopicWord.insert_many(topic_word_rows).execute()
            MaterialTopic.insert_many(lecture_topic_rows).execute()

    def lda_over_courses(self):
        """
        Perform LDA over all courses, no material/lecture level details.
        """

        courses = Course.select()
        courses_size = Course.select(Course.code).distinct().count()
        courses_dict = []
        for course in courses:
            course_words = CourseWord.select().where(CourseWord.course == course)
            courses_dict.append(dict([(x.word, x.count) for x in course_words]))

        print "Performing LDA over all courses.."
        model, vocab = self.__perform_lda_default(courses_dict, courses_size)

        log_likelihoods = []
        for i, x in enumerate(model.loglikelihoods_):
            row_dict = {'iteration': i * 10,
                        'loglikelihood': round(x, 2)}
            log_likelihoods.append(row_dict)

        topic_word_rows = []
        # Iterate over topic word distributions
        for i, topic_dist in enumerate(model.topic_word_):
            top_topic_words = np.array(vocab)[self.__max_values(topic_dist, self.n_top_words)]
            top_word_probs = topic_dist[np.argsort(topic_dist)][:-self.n_top_words - 1:-1]

            for top_word, top_weight in zip(top_topic_words, top_word_probs):
                row_dict = {'topic': i,
                            'word': top_word,
                            'weight': round(top_weight * 100, 2)}
                topic_word_rows.append(row_dict)

            if self.debug:
                top_word_str = ", ".join([x.encode('utf-8') + "(" + str(round(y * 100, 2)) + "%)"
                                         for x, y in zip(top_topic_words, top_word_probs)])
                print('Topic {}: {}'.format(i, top_word_str))

        # Document-topic distributions
        doc_topic = model.doc_topic_
        course_topic_rows = []
        for i in range(courses.count()):
            top_topics = np.argsort(doc_topic[i])[:-self.n_top_topic - 1:-1]
            topic_probs = doc_topic[i][top_topics]

            for top_topic, top_weight in zip(top_topics, topic_probs):
                row_dict = {'course': courses[i],
                            'topic': top_topic,
                            'weight': round(top_weight * 100, 2)}
                course_topic_rows.append(row_dict)

            if self.debug:
                doc_topic_str = ", ".join(
                    [str(x) + "(" + str(round(y * 100, 2)) + "%)" for x, y in zip(top_topics, topic_probs)])
                print("{} (top {} topics: {})".format(courses[i].name.encode('utf-8'),
                                                      self.n_top_topic, doc_topic_str))

        with db.atomic():
            LDALogLikelihood.insert_many(log_likelihoods).execute()
            TopicWord.insert_many(topic_word_rows).execute()
            CourseTopic.insert_many(course_topic_rows).execute()

    @staticmethod
    def __max_values(arr, top):
        indices = np.zeros(top, int)
        for i in xrange(top):
            idx = np.argmax(arr)
            indices[i] = idx
            arr[idx] = -1
        return indices

    def __perform_lda_default(self, word_dict, n_topics):
        # Initialize the "DictVectorizer" object, which is scikit-learn's
        # bag of words tool.
        vectorizer = DictVectorizer()

        # Init lda
        model = lda.LDA(n_topics=n_topics, n_iter=1000, random_state=1)

        return self.__perform_lda(word_dict, vectorizer, model)

    @staticmethod
    def __perform_lda(word_dict, vectorizer, model):
        # fit_transform() does two functions: First, it fits the model
        # and learns the vocabulary; second, it transforms our training data
        # into feature vectors(bag of words)
        train_data_features = vectorizer.fit_transform(word_dict)

        # Convert the result to an array
        train_data_features = train_data_features.toarray()

        # Get the vocabulary
        vocab = vectorizer.get_feature_names()

        # Print all the words and their counts
        # __print_word_dist(res)

        #Fit model
        model.fit(train_data_features.astype('int32'))

        return model, vocab

    @staticmethod
    def __print_word_dist(data):
        # Sum up the counts of each vocabulary word
        dist = np.sum(data['X'], axis=0)

        for tag, count in zip(data['vocab'], dist):
            print count, tag


if __name__ == '__main__':
    topic_model = TopicModeling()

    # Perform LDA over all courses
    topic_model.lda_over_courses()

    # Perform LDA over all material
    topic_model.lda_over_all_material()

    # Perform LDA over all material in scope of one course
    topic_model.lda_over_lectures()

    #Resolve topic names where possible
    TopicNameResolver2().name_topics()

