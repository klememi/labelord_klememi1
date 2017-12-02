Labelord
========
|travis| |rtd|

.. |travis| image:: https://travis-ci.org/klememi/labelord_klememi1.svg?branch=master
    :target: https://travis-ci.org/klememi/labelord_klememi1
    :alt: Build Status
.. |rtd| image:: https://readthedocs.org/projects/labelord-klememi1/badge/?version=latest
    :target: http://labelord-klememi1.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Labelord is small GitHub labels manager. Labels in configured repositories can be automatically kept in sync. This was coded as a school project at *FIT CTU* in Prague.

Installation
------------

1. via test.pypi_
    ``python -m pip install --extra-index-url https://test.pypi.org/pypi labelord_klememi1``

2. manually
    - download the package from GitHub repository_
    - unpack it
    - run ``python setup.py install``

.. _test.pypi: https://test.pypi.org
.. _repository: https://github.com/klememi/labelord_klememi1

Documentation
-------------

Please see full documentation on http://labelord-klememi1.rtfd.io/ for more information.

Optionally you can build *docs* yourself.

1. run ``python -m pip install -r docs/requirements.txt``
2. ``make html`` in **docs** folder to generate html
3. ``make doctest`` in **docs** folder to test documentation

License
-------

**MIT**
