"""
Based on original TopicNameResolver, but uses more advanced semantics to resolve a topic name.
The aim was to reduce the amount of "General" topics.
"""

from db.DataModel import db, CourseTopic, CourseTopicInfo
import string


class TopicNameResolver2(object):

    def __init__(self, weight_multiplier=1.5):
        self.weight_multiplier = weight_multiplier
        self.blacklist = [
            u'introduction to',
            u'introduction',
            u'research seminar in',
            u'seminar of',
            u'seminar on',
            u'seminar',
            u'project work',
            u'project',
            u'special course in',
            u'research in'
        ]

    def name_topics(self):
        topic_bucket = {}
        for topic_entry in CourseTopic.select():
            topic_id = topic_entry.topic
            if topic_id not in topic_bucket:
                topic_bucket[topic_id] = [topic_entry]
            else:
                topic_bucket[topic_id].append(topic_entry)

        rows = []
        for topic_id, topics in topic_bucket.items():
            rows.append({
                'topic': topic_id,
                'name': self.__resolve_topic_name(topics)
            })

        with db.atomic():
            CourseTopicInfo.insert_many(rows).execute()

        return rows

    def __resolve_topic_name(self, topic_courses):
        sorted_topics = sorted(topic_courses, key=lambda topic_course: topic_course.weight, reverse=True)
        total_weight = 0
        top_title = sorted_topics[0].course.name.strip().lower()
        second_weight = 0  # Weight of the course after top course(s)
        for topic in sorted_topics:
            if topic.course.name.strip().lower() == top_title:
                total_weight += topic.weight
            else:
                second_weight = topic.weight
                break

        if total_weight > second_weight * self.weight_multiplier:
            return self.__canonize_title(top_title)

        matching_words = self.__find_matching_word(sorted_topics)
        if matching_words:
            return matching_words
        return "General"

    def __find_matching_word(self, topic_courses):
        top_course_name = topic_courses.pop().course.name.split(' ')
        for topic_course in topic_courses:
            words = [word for word in top_course_name if len(word) > 3
                     and word.lower() in topic_course.course.name.lower()]
            new_name = ' '.join(words)
            if len(new_name) > 1 and not any(w in new_name.lower() for w in self.blacklist):
                return string.capwords(new_name)
        return ''

    def __canonize_title(self, title):
        title = title.lower()
        for w in self.blacklist:
            title = title.replace(w, '')

        # Remove all parenthesis
        start_idx = title.find('(')
        while start_idx != -1:
            end_idx = title.find(')', start_idx)
            title = title[:start_idx] + title[end_idx+1:]
            start_idx = title.find('(')

        # Remove arabic and roman numbers indicating course level
        title = filter(lambda x: not x.isdigit(), title)
        while title.endswith('i') or not (title[len(title)-1].isalpha() or title[len(title)-1] == '+'):
            title = title[:len(title)-1]

        # Remove symbols and everything irrelevant from the beginning
        while not title[0].isalpha():
            title = title[1:len(title)]

        return string.capwords(title.strip())


if __name__ == '__main__':
    print TopicNameResolver2().name_topics()
    # i = 1.0
    # while i <= 2.5:
    #     rows = TopicNameResolver2(i).name_topics()
    #     print str(i) + " " + str(sum(row["name"] == "General" for row in rows))
    #     i += 0.05
