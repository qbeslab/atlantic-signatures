=======================
Running Your First Test
=======================

.. todo:: Update (or more likely remove as obsolete) the test instructions.

You are now ready to run tests using the irobot Create for the Atlantic
Signatures project! The python package comes with a file titled: "demo.cfg",
this file is a configuration script and contains all the parameters relevant
to the atlantic signatures paper as well as parameters for how the Create is
run. For our first test we will use these default parameters before running
tests with custom parameters.

------
Step 1
------
Open up "anaconda prompt" on the host computer and ensure atlantic_signatures
has been properly installed by tying in: ``pip show atlantic_signatures``. If
nothing appears then redo all the steps for setting up the host computer.

A simple Command Line Interface (CLI) was installed with the atlantic_signatures
program and we will enter all commands inside the anaconda prompt.

------
Step 2
------
Using PuTTY, connect to the Raspberry Pi. The same CLI was also installed within
the virtual environment on the Raspberry Pi so we activate our virtual environment
instead of loading up anaconda prompt. To activate the virtual environment:

.. code-block:: bash

    source atlantic_signatures/venv/bin/activate

------
Step 3
------
We are now ready to run! Inside both PuTTY and anaconda prompt, type in the command:

.. code-block:: bash

    atlantic_signatures run

Note: There have been connectivity issues when the command is run first on the host.
It is recommended to run the above command in PuTTY, wait five seconds then run the
above command in anconda prompt.

Within about 10 seconds the Create should start moving in accordance to the parameters
found in the demo.cfg file. You may have to run the above command several times if
connectivity issues arise.

Once the test is complete (failure or success), a data file will be generated in a
aptly named directory titled 'data'. The data directory will be created at the location
the anaconda prompt was working at which should be the users home page (for me it is
C:\\Users\\lucsc).
