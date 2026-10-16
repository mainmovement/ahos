#!/bin/bash
cd /g/robat/ahos
python3 -m http.server 8080 > /tmp/server.log 2>&1 &
SERVER_PID=$!
sleep 2
echo $SERVER_PID
