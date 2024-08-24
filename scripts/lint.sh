#!/bin/bash

terraform fmt -recursive
pre-commit run --all-files
