#!/bin/bash

rm -rf ../out/input_*
rm -rf ../out/output_*
rm -rf ../log/*.log

echo "0 3
3 0
3 2
2 3
3 1
1 3
0 1
1 0
1 2
2 1" > ../topology

../src/node.py 0 sender "funny str" 20 & 
../src/node.py 1 20 & 
../src/node.py 2 20 & 
../src/node.py 3 receiver 0 20 &
../src/controller.py 25 &