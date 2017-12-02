.. _examples:

Examples
========

.. testsetup::

    from labelord.github import log_suc, log_err

Logging a successful action
---------------------------

.. doctest::

    >>> log_suc('ADD', 'SUC', 'labelord/repo1', 'Fix', '#afc100')
    [ADD][SUC] labelord/repo1; Fix; #afc100

Logging a successful dry action
-------------------------------

.. doctest::

    >>> log_suc('UPD', 'DRY', 'labelord/repo2', 'Todo', '#faa234')
    [UPD][DRY] labelord/repo2; Todo; #faa234

Logging an unsuccesful action
------------------------------

.. doctest::

    >>> log_err('DEL', 'labelord/repo3', 'C00L', '#435123', 400, 'BAD REQUEST')
    [DEL][ERR] labelord/repo3; C00L; #435123; 400 - BAD REQUEST
