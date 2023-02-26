from setuptools import setup

install_requires = [
]

long_description = """Python queue to process celery tasks and
                    enable retries when broker is down using a producer-consumer approach."""

setup(
    name='pyqueue_celery_processor',
    version="0.0.6",
    author="Fampay",
    author_email='tech@fampay.in',
    maintainer="Fampay",
    maintainer_email='tech@fampay.in',
    packages=['pyqueue_celery_processor'],
    license='MIT License',
    url="https://gitlab.com/fampay-oss/pyqueue-celery-processor",
    install_requires=install_requires,
    description='Python queue to process celery tasks.',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
