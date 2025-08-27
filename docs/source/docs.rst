===========================
Building This Documentation
===========================

This documentation can be built with Sphinx from the reStructuredText source
code. Sphinx_ is a Python-based documentation tool that compiles source files
written in a markup language into a static HTML website.

----------------
Building Locally
----------------

Requirements
------------

If you wish to build the documentation on your own computer, you will need to
install Python dependencies using the provided ``requirements-docs.txt``:

.. code-block:: bash

    pip install -r requirements-docs.txt

Manual Build
------------

You can manually trigger a build using the following command:

.. code-block:: bash

    sphinx-build docs/source docs/build/html

The resulting HTML files will be created in ``docs/build/html``.

Auto-Build
----------

The ``sphinx-autobuild`` tool installed with the other dependencies allows you
to launch a local web server that detects when documentation source files are
changed and saved, then auto-rebuilds the docs and auto-refreshes the local web
page in your browser, allowing you to immediately see the effects of your source
changes. Running the following command will start up the web server and open the
local docs in your browser:

.. code-block:: bash

    sphinx-autobuild docs/source docs/build/html --watch atlantic_signatures --ignore *__pycache__* --open-browser

Auto-Build with VS Code
-----------------------

Auto-building is made even easier in Visual Studio Code with the provided
``.vscode/launch.json`` file. It allows you to start up the same auto-build tool
with the click of a button in VS Code. Just navigate to the "Run and Debug" view
and start the "Sphinx Autobuild" configuration (Windows shortcut: F5).

-----------------------------
Documentation on GitHub Pages
-----------------------------

The `GitHub repository`_ is configured via ``.github/workflows/docs.yml`` to use
GitHub Actions to automatically build the documentation in the cloud and serve
it *publicly* using GitHub Pages.

.. warning::

    Because this copy of the documentation is public, you should not include
    sensitive information like passwords in this documentation!

This build process is triggered every time a code commit is pushed to the
repository on the ``main`` branch. This automatic process keeps the public copy
of the documentation found on GitHub up-to-date.

The public docs are found here: https://qbeslab.github.io/atlantic-signatures


.. _Sphinx: https://www.sphinx-doc.org
.. _`GitHub repository`: https://github.com/qbeslab/atlantic-signatures
