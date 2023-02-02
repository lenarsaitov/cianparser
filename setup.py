from setuptools import setup

setup(
    name='cianparser',
    version='0.4.2',
    description='Parser information from Cian website',
    url='https://github.com/lenarsaitov/cianparser',
    author='Lenar Saitov',
    author_email='lenarsaitov1@yandex.ru',
    license='MIT',
    packages=['cianparser'],
    classifiers=[],
    keywords='python parser requests cloudscraper beautifulsoup cian realstate',
    install_requires=['cloudscraper', 'beautifulsoup4', 'transliterate', 'pymorphy2', 'lxml', 'datetime'],
)
