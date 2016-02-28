from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Integer, String, DateTime,ForeignKey
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy import Sequence
from sqlalchemy import create_engine

Base = declarative_base()

class TableNameConvention(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class TimestampMixin(object):
    created_at = Column(DateTime, default=func.now())


class Tenant(TableNameConvention,Base):
    """
        Tenant - Services: one - to - many
    """
    id = Column(String(100),primary_key=True)
    name = Column(String(100))
    services = relationship("Service",back_populates="tenant")
    #init -> vm_created -> sa_provision
    state = Column(String(20))

class Service(TableNameConvention,TimestampMixin,Base):
    """
        Tenant - Service: one - to - many
    """
    id = Column(Integer, Sequence('service_id_seq'), primary_key=True)
    tenantId = Column(String(100),ForeignKey('tenant.id'))
    name = Column(String(20))
    os = Column(String(20))
    #the amount of instance that the tenant should have
    instancecount = Column(Integer)
    updatetime  = Column(DateTime)
    tenant = relationship("Tenant",uselist = False, back_populates="services")
    nodes = relationship("Node",back_populates="service")
    def isready(self):
        if len(self.nodes) == self.instancecount:
            return True
        else:
            return False
    def createnode(self):
        node = Node()
        node.serviceid = self.id
        node.vmtype = self.name
        return node



class Node(TableNameConvention,TimestampMixin,Base):
    serviceid = Column(Integer,ForeignKey('service.id'))
    stackid = Column(String(100),primary_key=True)
    hostname = Column(String(100))
    vmtype = Column(String(50))
    manageip = Column(String(30))
    serviceip = Column(String(30),nullable=True)
    publicip = Column(String(30))
    updatetime = Column(DateTime)

    service = relationship("Service",back_populates="nodes")

    jobs = relationship("RundeckJob",back_populates="service")


class RundeckJob(TableNameConvention,TimestampMixin,Base):
    id = Column(Integer, Sequence('rdeck_job_id_seq'), primary_key=True)
    nodeid = Column(String(100),ForeignKey('node.stackid'))
    name = Column(String(50))
    jobid = Column(String(100))
    jobstate = Column(String(50))
    service = relationship("Node",back_populates="jobs")


class DMSToolTask(TableNameConvention,TimestampMixin,Base):
    id = Column(Integer, Sequence('task_id_seq'), primary_key=True)
    accountId = Column(String(100))
    task_name = Column(String(50))
    state = Column(String(10))

if __name__ == '__main__':

  connect_url = "mysql+mysqldb://root:cisco123@127.0.0.1/dms"
  engine = create_engine(connect_url)

  Base.metadata.create_all(engine)
