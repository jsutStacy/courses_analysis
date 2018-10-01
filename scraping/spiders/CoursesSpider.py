# -*- coding: utf-8 -*-

import scrapy

from scraping.items import CoursesItem
from scraping.items import DataItem
from scraping.settings import ALLOWED_EXTENSIONS
from utils.SemesterUtils import parse_semesters
from utils.ConfigReader import Config


class CoursesSpider(scrapy.Spider):
    #Overridden params
    name = "courses"
    allowed_domains = []
    start_urls = []

    #Custom params
    allowed_semesters = []
    course_code = "";

    def __init__(self, semesters='', course_code='', *args, **kwargs):
        """ Expected format '2016F,2014S' - i.e 2016 fall semester and 2014 spring semester
            The 'semesters' parameter is passed via -a argument 
            The 'course_code' parameter is passed via -a argument """
        
        	
        super(CoursesSpider, self).__init__(*args, **kwargs)
        cfg = Config()
        course_info = cfg.get_courses_info()
        self.allowed_domains = course_info.get("allowed_domains")
        self.start_urls = course_info.get("start_urls")
        self.course_code = course_code

        # Commandline parameters override file parameters
        if semesters:
        	self.allowed_semesters = parse_semesters(semesters)
        else:
            self.allowed_semesters = cfg.get_allowed_semesters()

    def parse(self, response):
        for sel in response.xpath("//table[@class=\"table previous-years\"]/tr"):
            for it in sel.xpath(".//a"):
                link = it.xpath("@href").extract()[0]

                # Choose only wanted semesters
                for x in self.allowed_semesters:
                    if x[0] in link and x[1] in link:
                        filter_url = self.__determine_filter_url(response)
                        request = scrapy.Request(filter_url + ''.join(link), callback=self.parse_courses)
                        request.meta['filter'] = filter_url
                        request.meta['year'] = x[0]
                        request.meta['semester'] = x[1]
                        yield request

    def parse_courses(self, response):
    	print "parse_courses: {}".format(self.course_code)
    	if self.course_code != "":
    		for sel in response.xpath("//ul[@class=\"course-list\"]").xpath(".//li"):
    			code = sel.xpath(".//span/text()").extract()[0]
    			item = CoursesItem()
        		if (self.course_code == code):
        			print "FOUNDOCURSE: {}".format(self.course_code)
            		title = sel.xpath("a/text()").extract()[0]
            		item["title"] = title
            		item["link"] = ''.join(sel.xpath("a/@href").extract())
            		item["code"] = code
            		item["year"] = response.meta['year']
            		item["semester"] = response.meta['semester']
            		yield item
            		request = scrapy.Request(response.meta['filter'] + ''.join(item['link']), callback=self.parse_navbar)
            		request.meta['course'] = item
            		request.meta['year'] = response.meta['year']
            		request.meta['semester'] = response.meta['semester']
            		request.meta['filter'] = response.meta['filter']
            		yield request
    	else:
    		print "course_code not provided: {}".format(self.course_code)
        	for sel in response.xpath("//ul[@class=\"course-list\"]").xpath(".//li"):
        		item = CoursesItem()
            	title = sel.xpath("a/text()").extract()[0]
            	item["title"] = title
            	item["link"] = ''.join(sel.xpath("a/@href").extract())
            	item["code"] = ''.join(sel.xpath(".//span/text()").extract())
            	item["year"] = response.meta['year']
            	item["semester"] = response.meta['semester']
            	yield item
            	request = scrapy.Request(response.meta['filter'] + ''.join(item['link']), callback=self.parse_navbar)
            	request.meta['course'] = item
            	request.meta['year'] = response.meta['year']
            	request.meta['semester'] = response.meta['semester']
            	request.meta['filter'] = response.meta['filter']
            	yield request
        	
        	
        

    def parse_navbar(self, response):
        for sel in response.xpath("//nav[@class=\"sidebar\"]").xpath(".//a"):
            t_link = ''.join(sel.xpath("@href").extract())
            # only follow links in navbar that are inside allowed domain
            if t_link.find(response.meta['filter']) > -1:
                page_link = sel.xpath("@href").extract()
                request = scrapy.Request(''.join(page_link), callback=self.parse_article)
                request.meta['course'] = response.meta['course']
                request.meta['year'] = response.meta['year']
                request.meta['semester'] = response.meta['semester']
                request.meta['filter'] = response.meta['filter']
                yield request

    def parse_article(self, response):
        try:
            for sel in response.xpath("//article[@class=\"content\"]"):
                yield self.__create_data_item(response.url, sel.extract(), response)
        except AttributeError:
            pass

        for sel in response.xpath("//a"):
            t_link = ''.join(sel.xpath("@href").extract())
            if self.__is_valid_url(t_link):
                item = self.__create_data_item(sel.xpath("@href").extract(), '', response)
                item['title'] = sel.xpath("text()").extract()
                yield item

    def __determine_filter_url(self, response):
        filter_url = "https://" if "https:" in response.url else "http://"
        for domain in self.allowed_domains:
            if domain in response.url:
                filter_url += domain
                break

        return filter_url

    @staticmethod
    def __create_data_item(link, content, response):
        course = response.meta['course']

        item = DataItem()
        item['link'] = link
        item['path'] = ''.join(response.url).replace(response.meta['filter'], '') if not content else ''
        item['content'] = content
        item['course_code'] = course['code']
        item['year'] = response.meta['year']
        item['semester'] = response.meta['semester']

        return item

    @staticmethod
    def __is_valid_url(url):
        return url.endswith(ALLOWED_EXTENSIONS) and url.find("action=upload") == -1
