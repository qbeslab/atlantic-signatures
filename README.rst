===================
atlantic-signatures
===================

.. code-block:: bash

    # create an anaconda environment and install dependencies
    conda create -n robots -c conda-forge python=3.12 matplotlib sphinx sphinx_rtd_theme make ffmpeg git

    # activate the environment
    conda activate robots

    # download the package source code
    git clone https://github.com/qbeslab/atlantic-signatures.git

    # install the package (in develop mode)
    pip install -r atlantic-signatures\requirements.txt
    pip install -e atlantic-signatures

    # test that the atlantic_signatures command is installed
    atlantic_signatures --help

    # create an animated plot from a data file (test file required)
    atlantic_signatures plot Test-1.csv

    # run an experiment (run on client, wait 5 secs, then run on host)
    atlantic_signatures run

    # build the docs (after which they can be found in atlantic-signatures\docs\_build\html\index.html)
    make -C atlantic-signatures\docs clean && make -C atlantic-signatures\docs html
