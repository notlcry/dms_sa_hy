import os
from lib.services.servicecontext import ServiceContext
from jinja2 import FileSystemLoader,Environment


class WorkflowStep(object):
    pass

class CopyFileStep(WorkflowStep):
    def __init__(self,src,dst):
        self.src = src
        self.dst = dst

    def attach(self,job):
        job.addcopyfile(self.src,self.dst)

class ExecuteCommandStep(WorkflowStep):
    def __init__(self,command):
        self.cmd = command

    def attach(self,job):
        job.addcommand(self.cmd)

class ServiceFactory:
    @classmethod
    def createfactory(cls,svcname):
        return ServiceEventWFFactory(svcname)


class ServiceEventWFFactory(object):
    def __init__(self,servicename):
        self.servicename = servicename

    def createWFBuilder(self,eventType):
        if eventType == "SA_Provision":
            if self.servicename == "vrouter":
                return VRServiceEnableWFBuilder()
            elif self.servicename == "firewall":
                return FWServiceEnableWFBuilder()
            elif self.servicename == "ipsecvpn":
                return IPSecVPNServiceEnableWFBuilder()
            elif self.servicename == "dns":
                return DNSServiceEnableWFBuilder()


class WFBuilder(object):

    base_home = os.path.abspath(__file__)

    files_home = os.path.join(os.path.dirname(os.path.dirname(base_home)),"files")
    LOADER = FileSystemLoader(files_home)
    ENV = Environment(loader = LOADER)

    def __init__(self):
        config = ServiceContext().getConfigService()
        self.remote_path_base = config.get("File","remote_path")

    def _build_common(self,vmType,context):

        steps = []
        create_tmp_path = ExecuteCommandStep("if [ -d %s ];then rm -rf %s;fi;mkdir %s" % (self.remote_path_base,self.remote_path_base,self.remote_path_base))
        steps.append(create_tmp_path)
        file_home = os.path.join(self.files_home,vmType)
        typedb_path = os.path.join(file_home,"types.db")
        script_path = os.path.join(file_home,"python")
        post_step_path = os.path.join(file_home, "post_steps.sh")

        #first render the collectd conf
        template = self.ENV.get_template("%s/collectd.jnj2" % vmType)

        destpath = context["node_temp_home"]
        dest_file = os.path.join(destpath,"collectd.conf")
        with open(dest_file,"w+") as f:
            f.write(template.render(context))
        collectd_remote_path = os.path.join(self.remote_path_base,"collectd.conf")
        typesdb_remote_path = os.path.join(self.remote_path_base,"types.db")
        steps.append(CopyFileStep(dest_file,collectd_remote_path))
        steps.append(CopyFileStep(typedb_path,typesdb_remote_path))

        scripts = os.listdir(script_path)
        commands = []
        for script in scripts:
            remote_path = os.path.join(self.remote_path_base,script)
            steps.append(CopyFileStep(os.path.join(script_path,script),remote_path))
            dst_path = "/opt/collectd/lib/collectd"
            commands.append(ExecuteCommandStep("sudo cp  %s %s" % (remote_path,dst_path)))

        collectd_conf_command = ExecuteCommandStep("sudo cp  %s %s" %(collectd_remote_path,"/opt/collectd/etc"))
        typesdb_command = ExecuteCommandStep("sudo cp  %s %s" % (typesdb_remote_path,"/opt/collectd/share/collectd"))

        commands.append(collectd_conf_command)
        commands.append(typesdb_command)
        steps.extend(commands)

        steps.append(ExecuteCommandStep("sudo /opt/collectd/sbin/collectd"))

        log_courier_template = self.ENV.get_template("%s/log_courier/log.jnj2" % vmType)
        destpath = context["node_temp_home"]
        dest_file = os.path.join(destpath,"log-courier.conf")
        with open(dest_file, "w+") as f:
            f.write(log_courier_template.render(context))
        log_courier_remote_path = os.path.join(self.remote_path_base, "log-courier.conf")
        steps.append(CopyFileStep(dest_file, log_courier_remote_path))
        log_courier_conf_cmd = ExecuteCommandStep("sudo cp %s %s" % (log_courier_remote_path, "/etc/log-courier"))
        steps.append(log_courier_conf_cmd)

        post_step_remote_path = os.path.join(self.remote_path_base, "post_steps.sh")
        steps.append(CopyFileStep(post_step_path, post_step_remote_path))
        post_step_cmd = ExecuteCommandStep("sudo chmod +x /tmp/dms_sa/post_steps.sh")
        steps.append(post_step_cmd)
        return steps

class VRServiceEnableWFBuilder(WFBuilder):
    def buildWF(self,context):
        ctx = context["vrouter"]
        steps = []
        steps.append(ExecuteCommandStep("sudo pkill -9 collectd"))
        steps.extend(self._build_common("vrouter",ctx))
        steps.append(ExecuteCommandStep("sudo pkill -9 log-courier"))
        steps.append(ExecuteCommandStep("sudo /tmp/dms_sa/post_steps.sh"))
        return steps


class FWServiceEnableWFBuilder(WFBuilder):
    def buildWF(self,context):
        ctx = context["firewall"]
        steps = []
        steps.append(ExecuteCommandStep("sudo pkill -9 collectd"))
        steps.extend(self._build_common("firewall",ctx))
        steps.append(ExecuteCommandStep("sudo pkill -9 log-courier"))
        steps.append(ExecuteCommandStep("sudo service log-courier start"))
        steps.append(ExecuteCommandStep("sudo /tmp/dms_sa/post_steps.sh"))
        return steps

class IPSecVPNServiceEnableWFBuilder(WFBuilder):
    def buildWF(self,context):
        ctx = context["ipsecvpn"]
        steps = []
        steps.append(ExecuteCommandStep("sudo ps cax | grep collectd | wc -l; if [ $? != 0 ]; then pkill collectd;fi"))
        steps.extend(self._build_common("ipsecvpn",ctx))
        steps.append(ExecuteCommandStep("sudo pkill -9 log-courier"))
        steps.append(ExecuteCommandStep("sudo service log-courier start"))
        steps.append(ExecuteCommandStep("sudo /tmp/dms_sa/post_steps.sh"))
        return steps


class DNSServiceEnableWFBuilder(WFBuilder):
    def buildWF(self,context):
        ctx = context["dns"]
        steps = []
        steps.append(ExecuteCommandStep("sudo pkill -9 collectd"))
        steps.extend(self._build_common("dns",ctx))
        steps.append(ExecuteCommandStep("sudo pkill -9 log-courier"))
        steps.append(ExecuteCommandStep("sudo service log-courier start"))
        steps.append(ExecuteCommandStep("sudo /tmp/dms_sa/post_steps.sh"))
        return steps





