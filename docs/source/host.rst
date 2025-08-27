============================
Setting Up the Host Computer
============================

-------------------
Goals of this Guide
-------------------

#. Download and Install Anaconda

#. Install the atlantic_signatures package and its dependencies

Step 1: Get Anaconda
====================
Anaconda is an extremely useful python packaging ecosystem with a focus on
scientific applications of python. It is likely anaconda is already installled
on the host computer, to check this enter "anaconda prompt" in the search bar
if there are no hits then you should download and run the installer found at:
https://www.anaconda.com/products/distribution

Step 2: Install Atlantic Signatures project
===========================================
Launch an "anaconda prompt" terminal and navigate to the top level directory:
atlantic-signatures/ (this directory should could contain docs/ and vicon_dssdk/
amongst other directories. From this directory enter:

.. code-block:: batch

    pip install -e .[plot,docs]

The host computer is now setup! Everytime you wish to run tests, you will do
so from the anaconda prompt.
