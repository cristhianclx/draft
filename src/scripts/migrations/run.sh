#!/bin/bash

flask \
  --app function_app:_app \
  db upgrade
