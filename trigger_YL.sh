#!/bin/bash

m="ENABLE" && echo -e $(printf '\\x01\\x00\\x%02x\\x00%s' $((1 + ${#m})) "$m") | nc -q1 localhost 5555
