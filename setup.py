from setuptools import setup, find_packages
setup(
    name = "CoursesAnalysis",
    version = "1.0",
    packages = find_packages(),
    scripts = ['analyse_courses.sh','Makefile',
                'scrapy.cfg', 'requirements.txt'],

    package_data = {
        'cleaning': ['*.json'],
        'db': ['*.sqlite'],
    },
)