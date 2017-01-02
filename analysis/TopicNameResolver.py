"""
The intended goal of TopicNameResolver class is to assign each course-topic a name
based on courses that given topic covered the most. If no dominant course(>25%)
was found for a topic, a topic name 'General' is assigned instead.
"""

from db.DataModel import db, CourseTopic, CourseTopicInfo


class TopicNameResolver(object):

    def __init__(self):
        self.blacklist = [
            u'introduction to',
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
        topics = {}
        for topic_entry in CourseTopic.select():
            topic_id = topic_entry.topic
            if topic_id not in topics or topics[topic_id].weight < topic_entry.weight:
                topics[topic_id] = topic_entry

        rows = []
        for topic_id, topic in topics.items():
            rows.append({
                'topic': topic_id,
                'name': self.__resolve_topic_name(topic)
            })

        with db.atomic():
            CourseTopicInfo.insert_many(rows).execute()

        return rows

    def __resolve_topic_name(self, topic):
        if topic.weight < 25:
            return "General"

        name = topic.course.name.lower()
        for w in self.blacklist:
            name = name.replace(w, '')

        # Remove all parenthesis
        start_idx = name.find('(')
        while start_idx != -1:
            end_idx = name.find(')', start_idx)
            name = name[:start_idx] + name[end_idx+1:]
            start_idx = name.find('(')

        # Remove arabic and roman numbers indicating course level
        name = filter(lambda x: not x.isdigit(), name)
        while name.endswith('i') or not (name[len(name)-1].isalpha() or name[len(name)-1] == '+'):
            name = name[:len(name)-1]

        # Remove symbols and everything irrelevant from the beginning
        while not name[0].isalpha():
            name = name[1:len(name)]

        return name.strip().title()


if __name__ == '__main__':
    print TopicNameResolver().name_topics()