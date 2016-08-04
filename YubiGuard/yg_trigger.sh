#!/bin/bash

IP=127.0.0.1
PORT=5555
MSG="ON"

echo -e $(printf '\\x01\\x00\\x%02x\\x00%s' $((1 + ${#MSG})) "$MSG") | nc -q1 $IP $PORT