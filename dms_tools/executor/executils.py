import datetime
import time

def sync_runadhoc(client,project,command,timeout=10,check_interval=2,**kwargs):
    id = client.run_adhoc_command(project,command,**kwargs)
    delta = datetime.timedelta(seconds=timeout)
    now = datetime.datetime.now()
    overdue = now + delta
    while(datetime.datetime.now() < overdue):
        time.sleep(check_interval)
        output = client.execution_status(id)
        ret = check_output(output)
        if ret < 0:
            break
        elif ret == 0:
            continue
        else:
            return id
    print "Start failed, the execution id is %s" % id
    return -1

def wait_adhoc(client,idlist,timeout=10,check_interval=2):
    target = len(idlist)
    delta = datetime.timedelta(seconds=timeout)
    now = datetime.datetime.now()
    overdue = now + delta
    monitor = []
    while(datetime.datetime.now() < overdue):
        time.sleep(check_interval)
        for id in idlist:
            output = client.execution_status(id)
            ret = check_output(output)
            if ret == 0:
                monitor.append(id)
            elif ret < 0:
                print "Error: one execution(%s) error" % id
                return
        if len(monitor) == 0:
            return target
        idlist = list(monitor)
        monitor = []

    print "Error: wait task list timeout"
    return -1

def check_output(output):
     if output["status"] != "running":
        if output["status"] == "succeeded":
            href = output["href"]
            print "Start successfully, the output can check: %s" % href
            return 1
        else:
            return -1
     else:
         return 0