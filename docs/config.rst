.. _config:

Configuration
=============

.. _token:

Access token
------------
**Labelord** is working with *GitHub* so valid access token needs to be provided for the application to work properly. You can generate a new one `here <https://github.com/settings/tokens/new>`_. Make sure that **repo** scope is selected if you want to also manage your private repositories.

You can provide your token to application by 3 ways (sorted from lowest priority):

- Directive in configuration file, see :ref:`configfile` below
- Via environmental variable `GITHUB_TOKEN`
- `-t / --token` option of command-line application

**Do not forget that no one should know your personal token so never make it public!**

.. _webhook:

Webhook
-------
Labelord offers an option to handle changes on labels of your repositories automatically. In order to get this done you need to set up a webhook. From your template repository go to **Settings > Webhooks** and create a new one with these settings:

- Payload URL: IP address, where Labelord is running. If you don't own public IP, you can use free hosting services like `pythonanywhere.com <https://www.pythonanywhere.com>`_.  Default port is **5000**.
- Content type: **application/json**
- Secret: Your secret passphrase, which you also need to set in Labelord config. It's used to check that incoming request is from real GitHub.
- Trigger events: **label**

Copy your webhook secret to configuration file, as you can see below.

.. _configfile:

Configuration file
------------------
By default configuration file **config.cfg** is located in package root directory. It's structure looks like this::

    [github]
    token = <your_personal_token>
    webhook_secret = <your_webhook_secret>

    ; Repositories you wish to keep in sync
    [repos]
    owner/repo1 = on
    owner/repo2 = off

    ; Template labels names and color in hex
    [labels]
    label1 = ff0000
    label2 = 00ff00
    label3 = 0000ff

    ; Repository used as a template for labels. Has higher precedence than [labels]
    [others]
    template-repo = repoowner/labelsrepo

