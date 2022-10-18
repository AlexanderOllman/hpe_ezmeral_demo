#! /usr/bin/python
kill -9 `pidof python`
kill -9 `pidof python3`
kill -9 `pidof python3.6`
rm -f /mapr/my.cluster.com/teits/TelloPy/tellopy/_internal/*.pyc
rm -rf /mapr/my.cluster.com/teits/data/images/*