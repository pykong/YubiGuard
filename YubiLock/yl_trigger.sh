#!/bin/bash

IP=127.0.0.1
PORT=5555
m="ENABLE" && echo -e $(printf '\\x01\\x00\\x%02x\\x00%s' $((1 + ${#m})) "$m") | nc -q1 $IP $PORT