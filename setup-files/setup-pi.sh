#!/bin/bash
#
# Bash script to automate the setup of a python virtual environment with all the
# dependecies of the atlantic_signatures project

# The directory of the atlantic_signatures/
# This should be /home/pi/atlantic_signatures but we cannot assume the user
# won't accidentally transfer the package to a different directory
BASEDIR=`realpath $0 | xargs dirname | xargs dirname`
VENVDIR="$BASEDIR/venv"
VENVSITEPACKAGES="$VENVDIR/lib/python*/site-packages/"

# Create the virtual environment in the base directory
echo "Creating the atlantic_signatures virtual environment in $VENVDIR"
python -m venv $VENVDIR
echo Successfully created the atlantic_signatures virtual environment

cp -r /usr/lib/python3/dist-packages/numpy* $VENVSITEPACKAGES
echo Successfully copied system numpy to the virtual environment

cp -r /usr/lib/python3/dist-packages/serial* $VENVSITEPACKAGES
echo Successfully copied system pyserial to the virtual environment

# Activate the virtual environment python interpreter:
. $VENVDIR/bin/activate

pip install $BASEDIR/setup-files/Pint*.whl --no-deps

pip install -e $BASEDIR -U --no-deps --no-index

# Add a command to ~/.profile that automatically actives the virtual environment
PROFILE_FILE="$HOME/.profile"
if ! grep -q "atlantic-signatures" "$PROFILE_FILE"; then
    echo "Adding automatic environment activation to $PROFILE_FILE"
    echo "" >> "$PROFILE_FILE"
    echo "# activate the atlantic-signatures python virtual environment" >> "$PROFILE_FILE"
    echo "if [ -d \"$VENVDIR/bin\" ]; then" >> "$PROFILE_FILE"
    echo "    . \"$VENVDIR/bin/activate\"" >> "$PROFILE_FILE"
    echo "fi" >> "$PROFILE_FILE"
else
    echo "Automatic environment activation already found in $PROFILE_FILE"
fi
