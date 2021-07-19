from setuptools import setup

setup(
    name='python-parser-cian',
    version='0.1',
    description='Parser information from Cian website',
    url='https://github.com/lenarsaitov/cianparser',
    author='Lenar Saitov',
    author_email='lenarsaitov1@yandex.ru',
    license='MIT',
    packages=['cianparser'],
    classifiers=[],
    keywords='python parser requests beautifulsoup cian',
    install_requires=['requests', 'beautifulsoup4', 'transliterate', 'pymorphy2'],
)
