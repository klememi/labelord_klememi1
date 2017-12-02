.. Labelord documentation master file, created by
   sphinx-quickstart on Fri Dec  1 14:56:58 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Labelord's documentation!
====================================

So you have tons of GitHub repositories and you want all of them to have your cool custom labels but managing labels is hell, right? Not with *Labelord*! Setup necessary configuration and enjoy synchronized labels across all your repositories.

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

Configuration
-------------
- :ref:`token`
- :ref:`webhook`
- :ref:`configfile`

Usage
-----
- :ref:`cliusage`
- :ref:`webusage`

Examples
--------
:ref:`examples`

API reference
-------------

- :ref:`climodule`
- :ref:`githubmodule`
- :ref:`webmodule`
- :ref:`helpersmodule`

License
-------
:ref:`license`

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Contents:

   config
   usage
   examples
   api
   license
