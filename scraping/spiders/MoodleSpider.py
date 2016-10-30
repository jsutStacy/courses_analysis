# -*- coding: utf-8 -*-

from scraping.items import CoursesItem, DataItem
from scraping.settings import ALLOWED_EXTENSIONS
import scrapy
import datetime


class MoodleSpider(scrapy.Spider):
    #Overridden params
    name = "moodle"
    allowed_domains = ["moodle.ut.ee"]
    start_urls = ["https://moodle.ut.ee/course/index.php?categoryid=142"]

    #Custom params
    filter_url = "https://moodle.ut.ee"
    exclude_links = ['/mod/forum', 'mod/assign']
    login_msg = 'Palun sisene kasutajana'
    download_suffix = '?forcedownload=1'
    semester = {}

    def __init__(self, *args, **kwargs):
        super(MoodleSpider, self).__init__(*args, **kwargs)
        self.semester = self.__determine_semester()

    @staticmethod
    def __determine_semester():
        now = datetime.datetime.now()
        semester = 'fall' if 1 < now.month < 9 else 'spring'
        return {'year': str(now.year), 'semester': semester}

    def parse(self, response):
        request = scrapy.Request(response.url, callback=self.parse_courses)
        yield request  # First page

        for sel in response.xpath("//div[@class=\"paging\"][1]"):
            for it in sel.xpath('.//a[not(@class="next")]'):
                link = it.xpath("@href").extract()[0]
                request = scrapy.Request(link, callback=self.parse_courses)
                yield request

    def parse_courses(self, response):
        for sel in response.xpath("//div[@class=\"coursename\"]"):
            for it in sel.xpath('.//a'):
                link = it.xpath("@href").extract()[0]
                title, course_code = self.__extract_course_info(it.xpath("text()").extract()[0])
                if title and course_code and course_code.isupper():
                    item = CoursesItem()
                    item["title"] = title
                    item["link"] = link
                    item["code"] = course_code
                    item["year"] = self.semester['year']
                    item["semester"] = self.semester['semester']
                    yield item

                    request = scrapy.Request(link, callback=self.parse_single_course)
                    request.meta['course'] = item
                    yield request

    def parse_single_course(self, response):

        #First extract summary
        for sel in response.xpath("//div[@class=\"summary\"]"):
            yield self.__create_data_item(response.url, sel.extract(), response)

        for sel in response.xpath("//div[@role=\"main\"]"):
            login = sel.xpath("//div[@id=\"notice\"]").extract()
            if login and self.login_msg in login:
                return

            for sel_link in sel.xpath("//a"):
                link = self.__extract_link(sel_link)
                if not link:
                    continue

                if link.endswith(ALLOWED_EXTENSIONS):
                    yield self.__create_data_item(link, '', response)
                elif link.find(self.filter_url) > -1 and \
                        not any([x in link for x in self.exclude_links]):
                    request = scrapy.Request(link, callback=self.parse_course_link)
                    request.meta['course'] = response.meta['course']
                    yield request

    def parse_course_link(self, response):
        for sel in response.xpath("//div[@role=\"main\"]"):
            for sel_link in sel.xpath("//a"):
                link = self.__extract_link(sel_link)
                if not link:
                    continue

                if link.endswith(ALLOWED_EXTENSIONS):
                    yield self.__create_data_item(link, '', response)

    def __extract_link(self, link_item):
        ref = link_item.xpath("@href").extract()
        if not ref:
            return None

        link = ref[0]
        if link.endswith(self.download_suffix):
            link = link[:-len(self.download_suffix)]
        return link

    @staticmethod
    def __extract_course_info(course_info):
        """
        Splits the full title into course title and course code.
        E.g Infoturve (MTAT.07.028) would be split into 'Infoturve'
        and 'MTAT.07.028'
        :param course_info:
        :return: course title and course code
        """
        split = course_info.split('(')
        if len(split) < 2 or len(split[-1]) < 5:
            return None, None
        return ''.join(split[0].strip()), split[-1][:split[-1].find(')')].strip()

    def __create_data_item(self, link, content, response):
        course = response.meta['course']

        item = DataItem()
        item['link'] = link
        item['path'] = '/' + self.semester['year'] + '/' + self.semester['semester'] + '/moodle/' + course['code']
        item['content'] = content
        item['course_code'] = course['code']
        item['year'] = [self.semester['year']]
        item['semester'] = [self.semester['semester']]
        return item