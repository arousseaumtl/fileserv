#!/bin/sh

black -l 120 . \
&& flake8 --max-line-length=120 .
