#!/bin/sh
cd render
make clean && make
cp *.so ..
