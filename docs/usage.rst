.. _usage:

Usage
=====

.. _cliusage:

Command-line
------------
CLI part of the application provides one-time actions for listing labels, repositories and managing labels across your repositories. You can run CLI application with::

    labelord [OPTIONS] COMMAND [ARGS]

Options
^^^^^^^
-c, --config PATH       Path of the configuration file. Default **./config.cfg**
-t, --token STRING      GitHub access token.
--version               Shows Labelord version currently installed.
--help                  Shows help menu. 

Commands
^^^^^^^^

list_repos
~~~~~~~~~~
Prints all repositories which can be processed with provided token. Each repository on single line in format *owner/repo*.

list_labels <repository>
~~~~~~~~~~~~~~~~~~~~~~~~
Prints all current labels from the repository. Each one on single line in format **#XXXXXX name**, where *#XXXXXX* is label color in hex format.

run <mode>
~~~~~~~~~~~
Runs labels processing in one of the modes desribed below.

Modes
#####

update
    Labels are added or updated from the template.

replace
    Labels are completely overriden by the template ones, that means labels that are in the repository but not in template are deleted.

Options
#######
-r, --template-repo REPOSITORY      Defines repository that should be used as a template of labels.
-a, --all-repos                     Use all repositories for processing (can be obtained with ``list_repos``).
-d, --dry-run                       Doesn't make any changes to repositories, just prints actions.
-v, --verbose                       Turns on verbose mode, printing out all actions done.
-q, --quiet                         Turns on quiet mode, nothing will be printed.

Logging
#######
In **verbose** mode, every action done is printed on single line beginning with two `Tags`_. Last line is summary indicating number of successful operations done or number of errors if any.

If **quiet** mode is chosen, nothing is printed, success of operations can be checked from return value (0 successful, 10 errors occured).

If neither is chosen only summary line is printed after actions are done.

Tags
####
[ADD]
    Action of adding a label.
[UPD]
    Action of updating a label.
[DEL]
    Action of deleting a label.
[LBL]
    Action of reading a label from repository (if an error occured while doing this).
[DRY]
    Action done successfully in *dry-run* mode.
[SUC]
    Action done successfully on GitHub.
[ERR]
    Action raised an error.

run_server
~~~~~~~~~~
Starts web application locally.

Options
#######
-h, --host IP       Hostname specification, default **127.0.0.1**.
-p, --port PORT     Port specification, default **5000**.
-d, --debug         Flag turns on debug mode.

.. _webusage:

Web application
---------------
After you have started application locally or deployed remotely you can send `GET`_ or `POST`_ requests.

GET
^^^
Returns informations about the application and list of repositories configured for processing.

POST
^^^^
Responds on requests from GitHub webhook propagating any change on label from one repository to all others.
