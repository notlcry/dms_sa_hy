from lib.base.handlebase import HandleBase
from pydispatch import dispatcher
from lib.services.servicecontext import ServiceContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound


from lib.utils import register
from lib.domain.do import Tenant,Service

from lib.utils import logger
from lib.client.zkclient import DMSInventoryManager
from lib.domain.model import ModelManager
from lib.utils.constants import Tenant_Sate
from lib.events import EventFactory
from lib.services.servicecontext import ServiceContext

class ServiceHandler(HandleBase):

    def run(self):
        self._initializeSession()
        ctx = ServiceContext()
        queue = ctx.getQueueService()
        while(True):
            event = queue.get()
            dispatcher.send(signal=event.eventName,sender=event,session=self.session)


    def _initializeSession(self):
        config = ServiceContext().getConfigService()
        db_url = config.get("DB","mysql_url")
        engine = create_engine(db_url)
        self.sessionmaker = sessionmaker(bind=engine)
        self.session = self.sessionmaker()

@register
def handleCreate_VM(*args,**kwargs):
    event = kwargs["sender"]
    session = kwargs["session"]
    try:
        account = session.query(Tenant).filter(Tenant.id == event.accountId).one()
    except NoResultFound,e:
        logger.info("miss package activate message, no handle it")
        return

    logger.info("handling account[%s],create_vm[%s],stackid[%s]...." % (event.accountId,event.vmType,event.stackId))
    account.getSM().trigger("create_vm",tenant = account,payload=event)


@register
def handlePackage_Activate(*args,**kwargs):
    event = kwargs["sender"]
    session = kwargs["session"]
    accountId = event.accountId
    try:
        account = session.query(Tenant).filter(Tenant.id == accountId).one()
        logger.error("<%s> account is in db , need to clean.")
    except NoResultFound:
        logger.info("<%s> is new accountid , create tenant id in db" % accountId)
        tenant = Tenant()
        tenant.id = accountId
        tenant.name = "TBD"
        tenant.state = Tenant_Sate.INIT
        session.add(tenant)
        packageName = event.packageName
        manager = ModelManager()
        svcs = manager.listsvcbypath(packageName)
        if svcs is None:
          logger.error("package(%s) has no corresponding service definition..." % pkg_path)
          return
        else:
          for model_svc in svcs:
              servcie = createRuntimeService(model_svc,tenant.id)
              session.add(servcie)
          tenant.getSM().trigger("package_activate",tenant = tenant,payload = event)


@register
def handleTenant_Check(*args,**kwargs):
    event = kwargs["sender"]
    accountId = event.accountId
    session = kwargs["session"]
    try:
        account = session.query(Tenant).filter(Tenant.id == accountId).one()
        svclist = account.services
        flag = True
        for svc in svclist:
            flag = flag and svc.isready()
        if not flag:
            account.getSM().trigger("package_activate_timeout",tenant = account)
    except NoResultFound:
        logger.warning("account(<%s>) has been deleted, just ignore" )

@register
def handleTenant_SAEnable(*args,**kwargs):
    event = kwargs["sender"]
    session = kwargs["session"]
    accountId = event.accountId
    if accountId == None:
        logger.error("accountId is None, ignore the invalid request")
        return
    try:
        account = session.query(Tenant).filter(Tenant.id == accountId).one()
        logger.error("<%s> account is in db , need to clean.")
        return
    except NoResultFound:
        tenant = Tenant()
        tenant.id = accountId
        tenant.name = "TBD"
        tenant.state = Tenant_Sate.PACKAGE_ACTIVATE
        session.add(tenant)
        session.flush()
        inventory = DMSInventoryManager()
        try:
            inventory.start()
            services = inventory.getservice(accountId)
        except:
            logger.error("get account <%s> service from zookeeper failed" % accountId)
            return
        mgr = ModelManager()
        for svc in services:
            model_svc = mgr.getsvfdefbyname(svc)
            servcie = createRuntimeService(model_svc,tenant.id)
            session.add(servcie)
            session.flush()
        for svc in services:
            nodes = inventory.getinstancebyservice(accountId,svc)
            for node in nodes:
                node["topic"] = "dms.event.rundeck"
                msg_event = EventFactory.getEvent("CREATE_VM",node)
                tenant.getSM().trigger("create_vm",tenant = tenant,payload=msg_event)
        session.commit()
        inventory.stop()

@register
def handleTenant_Delete(*args,**kwargs):
    event = kwargs["sender"]
    accountId = event.accountId
    session = kwargs["session"]
    rdclient = ServiceContext().getRdClient()
    rdclient.api_version = 1
    try:
        account = session.query(Tenant).filter(Tenant.id == accountId).one()
        services = account.services
        for svc in services:
            nodes = svc.nodes
            for node in nodes:
                jobs = node.jobs
                for job in jobs:
                    try:
                        rdclient.delete_job(job.jobid)
                    except:
                        logger.warning("delete job(%s) error, just ignore any way" % job.jobid)
                    session.delete(job)
                session.delete(node)
            session.delete(svc)
        session.delete(account)
        session.commit()
        logger.info("delete account<%s>." % accountId)
    except NoResultFound:
        logger.warning("account(<%s>) has been deleted, just ignore" % accountId    )
    finally:
        del rdclient.api_version

def createRuntimeService(model_svc,tenantid):
    svc = Service()
    svc.tenantId = tenantid
    svc.instancecount = model_svc.instancecount
    svc.os = model_svc.os
    svc.name = model_svc.type
    return svc
