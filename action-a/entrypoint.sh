#!/bin/sh -l

sh -c "echo Hello world my name is $INPUT_MY_NAME"
# shellcheck disable=SC2088
cd ~/innerbloomBot
git pull
