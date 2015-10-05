#!/bin/sh

# This is a utility testing tool for Bugbase
# It will create a virtualenv to be sure there are no missing requirements, then will run the tests and linters

PYENV="${HOME}/.pyenv/bugbase"
PIP_DOWNLOAD_CACHE="${HOME}/.pip_download_cache"

# Absolute path to this script
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in
SCRIPTPATH=$(dirname "$SCRIPT")
# Absolute path bugbase is in
WORKSPACE=${WORKSPACE-`dirname "$SCRIPTPATH"`}

# clean previous build
if [ -d tests-results ]; then
    rm -rf tests-results
fi

if [ -d ${PYENV} ]; then
    rm -rf ${PYENV}
fi

if [ -f error.log ]; then
    rm error.log
fi

type virtualenv > /dev/null
if [ $? -ne 0 ]; then
    echo "Virtualenv is not installed and is required to run tests this way"
    exit 2
fi

# setup virtualenv
virtualenv -p `which python3` -q --no-site-packages ${PYENV}
. ${PYENV}/bin/activate

# install requirements
pip3 install -r conf/requirements.pip > /dev/null 2>&1
pip3 install -r tests/conf/requirements.pip > /dev/null 2>&1

cd ${WORKSPACE}

# configure tests
echo "[DEFAULT]" > conf/custom.conf
echo "default_directory = ${WORKSPACE}" >> conf/custom.conf
echo "show_progress = False" >> conf/custom.conf

python3 -m nitpycker --verbose --pattern="*test*.py" --with-coverage --cover-xml --cover-branch --with-xmlreporter --cover-no-stdout --with-textreporter .
error=$?

# run pylint
touch ${WORKSPACE}/__init__.py
pylint --rcfile=${WORKSPACE}/tests/conf/pylint.conf -f parseable ${WORKSPACE} > "${WORKSPACE}/tests-results/pylint.out"
rm ${WORKSPACE}/__init__.py

pep8 --max-line-length 120 *.py > "${WORKSPACE}/tests-results/pep8.out"

# this allows to set a pretty name for jenkins builds
echo "bugbase.version=`git log --pretty=format:%s --abbrev-commit -n1`" > .version.properties

exit ${error}
