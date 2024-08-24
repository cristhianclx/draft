#!/bin/bash

flask \
  --app function_app:_app \
  run \
  --host 0.0.0.0 \
  --port 7071 \
  --reload
