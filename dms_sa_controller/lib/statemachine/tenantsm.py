import os
from lib.services.servicecontext import ServiceContext
from .. client.dmskafka import DmsKafkaClient
from fysom import Fysom
from .. domain.jobbuilder import JobBuilder
from .. utils.constants import Tenant_Sate
from rundeck.client import Rundeck
from sqlalchemy.orm.session import object_session
from .. utils import logger
from lib.dsoSynczoo.account_sync_tran import account_sync

def create_tenant_sm(state=Tenant_Sate.INIT):
    sm = Fysom({'initial': state,
                'events':[
                {'name':'package_activate','src': Tenant_Sate.INIT,'dst':Tenant_Sate.PACKAGE_ACTIVATE},
                {'name':'create_vm','src':Tenant_Sate.PACKAGE_ACTIVATE,'dst':Tenant_Sate.VM_CREATE},
                {'name':'create_vm','src':Tenant_Sate.VM_CREATE,'dst':Tenant_Sate.VM_CREATE},
                {'name':'package_activate_timeout','src':[Tenant_Sate.INIT,Tenant_Sate.VM_CREATE,Tenant_Sate.PACKAGE_ACTIVATE],'dst':Tenant_Sate.PACKAGE_TIMEOUT},
                {'name':'create_vm_done','src':Tenant_Sate.VM_CREATE,'dst': Tenant_Sate.MONITOR_CPE},
                {'name': 'monitor_cpe_done','src': Tenant_Sate.MONITOR_CPE, 'dst': Tenant_Sate.SA_PROVISION},
                {'name': 'sa_prov_done','src': Tenant_Sate.SA_PROVISION, 'dst': Tenant_Sate.FINISH}
                ],
                'callbacks': {
                 'onservice_activing': serviceactivate,
                 'onreentervm_creating': vmcreate,
                 'onvm_creating': vmcreate,
                 'onmonitor_cpe': monitorcpe,
                 'onsa_provision': saprovisioning,
                 'onpackage_timeout': packagetimeout
                }})
    return sm

#prevent reenter the state when loading from db
def guard(func):
    def _handler(e):
        if e.src == "none":
            return
        else:
            func(e)
    return _handler

@guard
def serviceactivate(e):
    tenant = e.tenant
    session = object_session(tenant)
    JobBuilder.addschedcheckjob(tenant.id)
    tenant.state = e.fsm.current
    ctx = ServiceContext()
    tenant_path = os.path.join(ctx.getConfigService().get("File","local_temp_path"),tenant.id)
    if not os.path.exists(tenant_path):
        os.makedirs(tenant_path)
    session.flush()
    session.commit()
    logger.info("Account: %s [Package_Activate] handle successfully" % tenant.id)


@guard
def vmcreate(e):
    tenant = e.tenant
    msg = e.payload
    session = object_session(tenant)
    svc = tenant.getservicebyname(msg.vmType)

    if svc is None:
        logger.error("for node(%s/%s/%s) can not find corresponding service db object" % (tenant.id,msg.vmType,msg.stackid))
        return

    logger.info("part sync start.accountId<%s>" % tenant.id)
    ctx = ServiceContext()
    zk_host = ctx.getConfigService().get("Inventory","zk_address")
    account_sync(tenant.id,zk_host)
    logger.info("part sync finished.accountId<%s>" % tenant.id)
    node = svc.createnode()
    node.stackid = msg.stackId
    node.vmtype = msg.vmType
    node.manageip = msg.vmManagementIP
    node.publicip = msg.vmPublicIP
    node.serviceip = msg.vmServiceIP
    session.add(node)
    session.commit()
    logger.info("node(%s/%s/%s) has been created in db" % (tenant.id,node.vmtype,node.stackid))
    flag = True
    for svc in tenant.services:
        flag = flag and svc.isready()

    tenant.state = e.fsm.current

    if flag:
        tenant.getSM().trigger("create_vm_done",tenant = tenant)




def monitorcpe(e):
    tenant = e.tenant
    job = JobBuilder.buildmonitorcpejob(tenant)
    rundeck_client = ServiceContext().getRdClient()
    session = object_session(tenant)
    if job is None:
        logger.error("monitor cpe job build failded")
        return
    try:
        rundeck_reponse = rundeck_client.import_job(job.to_xml(),fmt = "xml", dupeOption = "create" , project = "dms-sa", uuidOption = "remove")
    except:
        logger.error("import account(%s) job failed, for connection reason" % tenant.id)
        session.flush()
        return

    if rundeck_reponse['failed'] == None and rundeck_reponse['skipped'] == None:
        print rundeck_reponse
        id = rundeck_reponse['succeeded'][0]["id"]
        name = rundeck_reponse['succeeded'][0]["name"]
        rdjob = job.node.createrdjob(name,id)
        session.add(rdjob)
        try:
            ret = rundeck_client.run_job(rdjob.jobid)
        except Exception,e:
            logger.error("runjob (%s) error (%s)" % (rdjob.jobid,e.message))
        else:
            status = ret['status']
            if status == 'falied':
                rdjob.jobstate = "runerror"
                href = ret["href"]
                logger.error("job run error , the execution link: (%s)" % href)
            else:
                rdjob.jobstate = "runsuccess"
        session.flush()

#    runjob(rundeck_client,job)
    #TDB: whether to wait for monitor cpe done
    tenant.state = e.fsm.current
    tenant.getSM().trigger("monitor_cpe_done",tenant=tenant)
    session.commit()


#{'status': 'failed', 'permalink': '', 'description': 'sudo pkill -9 collectd [... 20 steps]', 'project': 'dms-sa', 'job': {'permalink': 'http://10.74.125.196:4440/project/dms-sa/job/show/a37a0256-364d-4a1c-88c8-a1da2d498840', 'group': '05f813d1-4dd6-4d66-9c07-04a67527be20', 'name': '[vrouter]10.74.125.196:(SA_Provision)', 'project': 'dms-sa', 'href': 'http://10.74.125.196:4440/api/15/job/a37a0256-364d-4a1c-88c8-a1da2d498840', 'id': 'a37a0256-364d-4a1c-88c8-a1da2d498840', 'description': None}, 'href': 'http://10.74.125.196:4440/project/dms-sa/execution/show/13', 'user': 'admin', 'argstring': None, 'date-ended': datetime.datetime(2016, 1, 27, 7, 54, 24), 'date-started': datetime.datetime(2016, 1, 27, 7, 54, 23), 'id': '13'}
def saprovisioning(e):
    tenant = e.tenant
    jobs = JobBuilder.buildsaenablejobs(tenant)
    session = object_session(tenant)
    rundeck_client = ServiceContext().getRdClient()
    for job in jobs:
        try:
            rundeck_reponse = rundeck_client.import_job(job.to_xml(),fmt = "xml", dupeOption = "create" , project = "dms-sa", uuidOption = "remove")
        except:
            logger.error("import account(%s) job failed, for connection reason" % tenant.id)
            session.flush()
            return

        if rundeck_reponse['failed'] == None and rundeck_reponse['skipped'] == None:
            print rundeck_reponse
            id = rundeck_reponse['succeeded'][0]["id"]
            name = rundeck_reponse['succeeded'][0]["name"]
            rdjob = job.node.createrdjob(name,id)
            session.add(rdjob)
            try:
                ret = rundeck_client.run_job(rdjob.jobid)
            except Exception,e:
                logger.error("runjob (%s) error (%s)" % (rdjob.jobid,e.message))
                rdjob.jobstate = "runerror"
            else:
                status = ret['status']
                if status == 'falied':
                    rdjob.jobstate = "runerror"
                    href = ret["href"]
                    logger.error("job run error , the execution link: (%s)" % href)
                else:
                    rdjob.jobstate = "runsuccess"
            session.flush()

    #TBD:

    tenant.state = e.fsm.current
    tenant.getSM().trigger("sa_prov_done",tenant=tenant)
    session.commit()

def packagetimeout(e):
    tenant = e.tenant
    kafka = DmsKafkaClient()
    kafka.sendPackageTimeout(tenant.id)
    tenant.state = e.fsm.current
    session = object_session(tenant)
    session.flush()
    session.commit()
    logger.info("detect package timeout")
    #TBD,just send to zabbix alarm

