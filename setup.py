from distutils.core import setup

setup(
    name='QualysReporting',
    version='0.2.3',
    install_requires=["requests", "sqlalchemy", "psycopg2"],
    packages=['qgreports', 'qgreports.config', 'qgreports.scripts',
              'qgreports.utils'],
    data_files=['config/qualys-scan-mapping.json',
                'config/qualys-scan-mapping.json'],
    url='',
    license='',
    author='dmwoods38',
    author_email='',
    description=''
)
