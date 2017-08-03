#! /usr/bin/env bash

# Creates tarballs with a binary egg file and setup.py for python2/3,
# as well as binary wheel files.
#
# After unpacking, the resulting egg file can be installed with
# python setup.py easy_install wallycore*.egg
#
# The wheel file can be installed with
# pip install wallycore*.whl
#
# Like all tools/ scripts, this should be run from the project root.

set -e

PLATFORM=$(python -c "from distutils import util; print(util.get_platform().replace('-','_').replace('.','_'))")
NAME="wallycore-$PLATFORM"

function build {
    ./tools/cleanup.sh
    virtualenv -p $1 .venv
    source .venv/bin/activate

    # Create an egg from a new wally build
    PYTHONDONTWRITEBYTECODE= $1 setup.py install
    cp setup.py dist
    mv dist $NAME-$1
    tar czf $NAME-$1.tar.gz $NAME-$1
    sha256sum $NAME-$1.tar.gz >$NAME-$1.tar.gz.sha256

    # Create a wheel from the .egg
    cd $NAME-$1
    wheel convert *.egg
    WHEEL_NAME=$(ls *whl | sed "s/-any/-$PLATFORM/")
    mv *.whl ../$WHEEL_NAME
    cd ..
    sha256sum $WHEEL_NAME > $WHEEL_NAME.sha256
    #gpg --armor --output $NAME-$1.tar.gz.asc --detach-sign $NAME-$1.tar.gz
    #gpg --armor --output $WHEEL_NAME.asc --detach-sign $WHEEL_NAME
    rm -r $NAME-$1
    deactivate
}

build python2
build python3

./tools/cleanup.sh
