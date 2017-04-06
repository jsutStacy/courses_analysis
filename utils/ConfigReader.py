import ConfigParser
import os
from SemesterUtils import parse_semesters


class Config(object):
    def __init__(self):
        self.path = os.path.dirname(os.path.abspath(__file__)) + '/config.cfg'
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.path)

    def get_courses_info(self):
        params = dict(self.config.items("courses"))
        params['allowed_domains'] = params['allowed_domains'].split(';')
        params['start_urls'] = params['start_urls'].split(';')
        return params

    def get_moodle_info(self):
        params = dict(self.config.items("moodle"))
        params['allowed_domains'] = params['allowed_domains'].split(';')
        params['start_urls'] = params['start_urls'].split(';')
        return params

    def get_allowed_semesters(self):
        return parse_semesters(self.config.get("general", "allowed_semesters"))


if __name__ == '__main__':
    conf = Config()
    print conf.get_courses_info()
    print conf.get_moodle_info()
    print conf.get_allowed_semesters()