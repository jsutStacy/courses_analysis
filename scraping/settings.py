# -*- coding: utf-8 -*-

# Scrapy settings for tutorial project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'scraping'

SPIDER_MODULES = ['scraping.spiders']
NEWSPIDER_MODULE = 'scraping.spiders'
DOWNLOAD_TIMEOUT = 180

DOWNLOAD_HANDLERS = {
    's3': None,
}

ITEM_PIPELINES = {
    'scraping.pipelines.CoursePipeline': 300,
    'scraping.pipelines.DataPipeline': 400
}

ALLOWED_EXTENSIONS = ('.6up.pdf', '.pdf', '.pptx', '.docx', '.tex')