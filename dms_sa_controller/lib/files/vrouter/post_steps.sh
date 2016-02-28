#!/bin/bash
echo "post actions"
nohup journalctl -f | log-courier -config /etc/log-courier/log-courier.conf -stdin >/dev/null 2>&1 &
