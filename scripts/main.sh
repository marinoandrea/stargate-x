#!/usr/bin/sh

ARGS0=("$@")
ARGS1=("${ARGS[@]:1}")

while getopts "abp" opts;
do
case "${opts}" in
    a) SCRIPT="scripts/python/analyze.py";;
    b) SCRIPT="scripts/python/build.py";;
    p) SCRIPT="scripts/python/plot.py";;
    *) echo "Reactome graph error: no option given" >> stderr && exit 1;;
esac
done

# run script from project root folder
cp "$SCRIPT" t.py
python t.py ${ARGS1[@]}
rm t.py