#!/bin/bash

rm -rf ../out/input_*
rm -rf ../out/output_*
rm -rf ../out/*_received_from_*
rm -rf ../log/*.log

echo "0 1
1 2
2 3
3 0" > ../topology

../src/node.py 0 sender "funny str" 66 &
../src/node.py 1 66 &
../src/node.py 2 66 &
../src/node.py 3 receiver 0 66 &
../src/controller.py 65 &
