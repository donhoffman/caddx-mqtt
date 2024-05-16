from setuptools import setup

from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'DETAILS.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='caddx_mqtt',
      version='0.1.0',
      description='Caddx Interface Library and Server with MQTT client',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='donhoffman',
      url='https://github.com/donhoffman/caddx-mqtt',
      packages=['caddx_mqtt'],
      install_requires=['paho-mqtt', 'requests', 'pyserial', 'flask', 'prettytable'],
      scripts=['caddx_server', 'caddx_client'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3.11',
      ]
      )
