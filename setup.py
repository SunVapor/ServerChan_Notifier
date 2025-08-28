from setuptools import setup

setup(
    name="serverchan-notifier",
    version="1.0.0",
    description="ServerChan wechat notifier library",
    py_modules=["serverchan_notifier"],
    install_requires=["requests>=2.25.0"],
)
