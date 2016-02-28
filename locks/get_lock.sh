#! /bin/bash
lock=0
timeout=60
while [ ! $lock -eq 1 ]
do
  now=`date +%s`
  let timestamp=$now+$timeout+1
  lock=`redis-cli SETNX lock.dms $timestamp`
  echo $lock
  if [ $lock -eq 1 ];then
    break;
  else
    get=`redis-cli GET lock.foo`
    getset=`redis-cli GETSET lock.foo $timestamp`
    if [[ $now -ge $get && $now -ge $getset ]];then
      break;
    else
      sleep 10
    fi
  fi 
done
