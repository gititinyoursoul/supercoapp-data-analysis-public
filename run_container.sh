#! /bin/bash

docker run -it --mount type=bind,source="$(pwd)",target=/app debian_ipython