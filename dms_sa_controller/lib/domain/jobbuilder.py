from datetime import datetime,timedelta
import os

from .. domain.model import ModelManager
import factory
from job import Job
from lib.services.servicecontext import ServiceContext
from .. utils import logger
from lib.events import EventFactory

def checksvc(accountid):
    ctx = ServiceContext()
    queue = ctx.getQueueService()
    map = {"accountId":accountid,"eventName":"TENANT_CHECK"}
    event =  EventFactory.getEvent("TENANT_CHECK",map)
    queue.put(event)
    logger.info("trigger account(%s) tenant check" % accountid)

class JobBuilder:

    @classmethod
    def addschedcheckjob(cls,accountid):
        ctx = ServiceContext()
        sched = ctx.getSchedServcie()
        config = ctx.getConfigService()
        interval = config.get("Orchestrator","tenant_check_interval")
        now = datetime.now()
        delta = timedelta(seconds=int(interval))
        runtime = now + delta
        sched.add_job(checksvc,args=(accountid,),run_date=runtime)

    @classmethod
    def buildmonitorcpejob(cls,tenant):
        ctx = ServiceContext()
        config = ctx.getConfigService()
        host = config.get("monitorcpe","host")
        cmd = config.get("monitorcpe","command")
        lockcmd = config.get("monitorcpe","getlock")
        releasecmd = config.get("monitorcpe","releaselock")
        svclist = tenant.services
        for svc in svclist:
            if svc.name == "vrouter":
                nodes = svc.nodes
                for node in nodes:
                    job = Job()
                    job.node = node
                    job.setNodeFilter(host)
                    job.setGroup(tenant.id)
                    job.setName("MonitorCPETest")
                    job.addlocalcommand(lockcmd)
                    job.addcommand(cmd + " -c 6620e868-e9df-4c8d-8c74-87fe364f7222 -l 10.74.113.116 -r 10.74.113.117 -x 204 -y 205")
                    job.addcommand(releasecmd)
                    return job


        return None

    @classmethod
    def buildsaenablejobs(cls,tenant):
        context = cls._buildcontext(tenant)
        svclist = tenant.services
        jobs = []

        for svc in svclist:
            if svc.name == "vpc":
                continue
            nodes = svc.nodes
            for node in nodes:
                job = Job()
                job.node = node
                job.nodeId = node.stackid
                job.setGroup(tenant.id)
                job.setName("[%s]%s:(%s)" % (node.vmtype,node.manageip,"SA_Provision"))
                job.setNodeFilter(node.manageip)
                WF= factory.ServiceFactory.createfactory(svc.name).createWFBuilder("SA_Provision").buildWF(context)
                if len(WF) == 0:
                    logger.info("no need to run job(%s), becasue no work flow" % "[%s]%s:(%s)" % (node.vmtype,node.manageip,"SA_Provision"))
                    continue
                for step in WF:
                    step.attach(job)
                print job.to_xml()
                jobs.append(job)
        return jobs


    @classmethod
    def _buildcontext(cls,tenant):
        """
        build {svc:context}
        :param tenant:
        :return:
        """
        svclist = tenant.services
        modelmgr = ModelManager()
        svcmap = {}
        context = {}
        config = ServiceContext().getConfigService()
        tenant_path = os.path.join(config.get("File","local_temp_path"),tenant.id)
        items = config.items("Agent")
        paras = {}
        for key,value in items:
            paras[key] = value

        for svc in svclist:
            svcmap[svc.name] = svc
            context[svc.name] = {}

        for svc in svclist:
            if svc.name == "vpc":
                logger.info("build sa jobs--skip the vpc")
                continue
            svcdef = modelmgr.getsvfdefbyname(svc.name)
            sn = svcdef.service_neighbors
            mn = svcdef.manage_neighbors
            global_para = paras.copy()
            if config.has_section(svc.name):
                items = config.items(svc.name)
                for key,value in items:
                    global_para[key] = value
            ctx = context[svc.name]
            ctx["neighbors_manageip"] = []
            ctx["neighbors_serviceip"] = []
            ctx["account_id"] = tenant.id
            ctx.update(global_para)
            instances = svc.nodes
            for instance in instances:
                ctx["host_name"] = instance.manageip
                ctx["vm_type"] = svc.name
                node_path = os.path.join(tenant_path,instance.manageip)
                if not os.path.exists(node_path):
                    os.makedirs(node_path)
                ctx["node_temp_home"] = node_path

            for nb in sn:
                corrresponding_svc = svcmap[nb]
                nodes = corrresponding_svc.nodes
                for node in nodes:
                    if node.serviceip is not None:
                         ctx["neighbors_serviceip"].append(node.serviceip)

            for nb in mn:
                corrresponding_svc = svcmap[nb]
                nodes = corrresponding_svc.nodes
                for node in nodes:
                    ctx["neighbors_manageip"].append(node.manageip)

            ctx["neighbors_manageip"] = ",".join(ctx["neighbors_manageip"])
            ctx["neighbors_serviceip"] = ",".join(ctx["neighbors_serviceip"])

            ctx["os"] = svcdef.os

        return context

