from setuptools import setup

setup(
    name='cianparser',
    version='0.3',
    description='Parser information from Cian website',
    url='https://github.com/lenarsaitov/cianparser',
    author='Lenar Saitov',
    author_email='lenarsaitov1@yandex.ru',
    license='MIT',
    packages=['cianparser'],
    classifiers=[],
    keywords='python parser requests beautifulsoup cian',
    install_requires=['requests', 'beautifulsoup4', 'transliterate', 'pymorphy2', 'lxml'],
)
