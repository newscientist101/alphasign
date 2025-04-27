from setuptools import setup, find_packages
import sys

# Determine PyUSB version requirement based on Python version
if sys.version_info >= (3, 9):
    pyusb_req = 'pyusb>=1.0.0'
else:
    pyusb_req = 'pyusb>=1.0.0,<=1.2.1'  # 1.3.1+ requires Python 3.9+

setup(
  name = 'alphasign',
  version = '1.1.0',
  packages = find_packages(),
  install_requires = ['pyserial>=2.4', pyusb_req, 'pyyaml>=3.05'],
  author = 'Matt Sparks',
  author_email = 'ms@quadpoint.org',
  description = 'Implementation of the Alpha Sign Communications Protocol',
  long_description = ('Implementation of the Alpha Sign Communications '
                      'Protocol, which is used by many commercial LED signs, '
                      'including the Betabrite. Ported to Python 3.8+.'),
  url = 'https://github.com/msparks/alphasign',
  license = 'BSD',
  python_requires='>=3.8',
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Topic :: Software Development :: Libraries',
    'Topic :: Hardware :: Hardware Drivers',
  ],
)
