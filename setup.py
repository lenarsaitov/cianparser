from setuptools import setup

setup(
    name='cianparser',
    version='0.4.8',
    description='Parser information from Cian website',
    url='https://github.com/lenarsaitov/cianparser',
    author='Lenar Saitov',
    author_email='lenarsaitov1@yandex.ru',
    license='MIT',
    packages=['cianparser'],
    long_description=['file: README.md'],
    long_description_content_type=['text/x-rst; charset=UTF-8'],
    classifiers=[],
    keywords='python parser requests cloudscraper beautifulsoup cian realstate',
    install_requires=['cloudscraper', 'beautifulsoup4', 'transliterate', 'lxml', 'datetime'],
)
