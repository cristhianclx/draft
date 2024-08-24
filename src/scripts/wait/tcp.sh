#!/bin/bash

until nc -z $1 $2
do
  echo "$1 ... waiting"
  sleep 1
done
echo "$1 is ready"
