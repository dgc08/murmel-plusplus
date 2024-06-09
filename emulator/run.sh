#!/usr/bin/env sh

cd $(dirname "$(readlink -f "$0")")
rm multiplier.mur
cp ../examples/multiplier.mur .

make && echo "\n" && ./emulator
