import datetime

from setuptools import setup

now = datetime.datetime.now()
__version__ = "{}.{}.{}".format(now.year, now.month, now.day)
__version_tuple__ = (now.year, now.month, now.day)

with open("sinaraml/_version.py", "w") as fd:
    fd.writelines(
        [
            '__version__ = "{}"\n'.format(__version__),
            "__version_tuple__ = {}\n".format(__version_tuple__),
        ]
    )

setup(
    version=__version__,
)
