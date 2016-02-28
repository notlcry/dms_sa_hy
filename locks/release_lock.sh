#! /bin/bash
now=`date +%s`
timestamp=`redis-cli GET lock.foo`
if [ $now -lt $timestamp ];then
   redis-cli DEL lock.foo
fi
