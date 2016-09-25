#!/bin/sh

export PYTHONPATH=$(pwd)

: ${VERSIONS:="python python3"}

for module in test_gmail test_message
do
    echo "===" $module
    for py in $VERSIONS
    do
        echo "Testing:" $($py --version 2>&1)
        $py -m gmail.$module -v 
    done
done

