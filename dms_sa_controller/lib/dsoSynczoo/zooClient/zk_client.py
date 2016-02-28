# coding: utf-8

from kazoo.client import KazooClient
import logging
import json


class ZookClient(object):
    def __init__(self, zookeeper_host=None):

        logging.basicConfig()
        # Create a client and start it
        if zookeeper_host is None:
            zookeeper_host = "localhost:2181"
        self.zk = KazooClient(zookeeper_host)
        self.zk.start()
        self.tran = self.zk.transaction()
        self.CONST_BASE_PATH = "/dso/"
        self.CONST_ACCOUNTS_PATH = "accounts/"
        self.CONST_GROUPS_PATH = "groups/"
        self.CONST_USERS_PATH = "users/"
        self.CONST_HOSTS_PATH = "hosts/"
        self.CONST_SERVERS_PATH = "servers/"
        self.CONST_SERVICES_PATH = "services/"
        self.CONST_INSTANCES_PATH = "instances/"

        self.CONST_MAPPING_PATH = "Mapping/"
        self.CONST_IP2USER_PATH = "Ip2User/"
        self.CONST_MAC2USER_PATH = "Mac2User/"
        self.CONST_IP2VMPATH = "Ip2Vm/"
        self.CONST_USER2ACCOUNT_PATH = "User2Account/"
        self.CONST_AID2ANAME_PATH = "Aid2Aname/"
        self.CONST_VM_INFO_PATH = "VmInfo/"

        self.CONST_HOST_MAPPING = dict(vrouter='fedora', dns='ubuntu', firewall='ubuntu', ipsecvpn='centos', vpc='ubuntu')

    def create_accounts_path(self, accounts, **kwargs):
        # create accounts path
        accounts_path = self.CONST_BASE_PATH + self.CONST_ACCOUNTS_PATH
        self.zk.ensure_path(accounts_path)

        for account in accounts:
            # path = accounts_path + account.account_name
            path = accounts_path + account.id
            account_val = account.to_str()
            self.zk.ensure_path(path)
            self.zk.set(path, b"" + account_val.encode('utf8'))

    def create_account_path(self, account_info):
        """
            the path to a account
            :param account_info:
        """
        # create accounts path
        accounts_path = self.CONST_BASE_PATH + self.CONST_ACCOUNTS_PATH
        if not self.zk.exists(accounts_path):
            self.zk.ensure_path(accounts_path)

        path = accounts_path + account_info.id
        account_data = dict(id=account_info.id,
                            name=account_info.account_name)
        self.zk.ensure_path(path)
        self.zk.set(path, b"" + json.dumps(account_data).encode('utf8'))

    def create_accountinfo_path(self, account_info):
        account_path = self.CONST_BASE_PATH + self.CONST_ACCOUNTS_PATH + account_info.id + "/"
        if not self.zk.exists(account_path):
            print "Path" + account_path + " does not exist."

        # create groups path
        groups_path = account_path + self.CONST_GROUPS_PATH
        self.zk.ensure_path(groups_path)

        # set each group
        for group_item in account_info.groups:
            self.create_usergroup_path(groups_path, group_item)

        # create service path
        services_path = account_path + self.CONST_SERVICES_PATH
        self.zk.ensure_path(services_path)

        # set services summary
        self.gen_services_summay(services_path, account_info.services)

        # set each service
        for service_item in account_info.services:
            self.create_service_path(services_path, service_item)

    def create_service_path(self, parent_path, service):
        if service is None or service.servicename is None:
            return
        service_path = parent_path + service.servicename + "/"
        # service_data = "id: " + service.id + "\nservicename: " + service.servicename
        service_data = dict(id=service.id, servicename=service.servicename)

        self.zk.ensure_path(service_path)
        self.zk.set(service_path, b"" + json.dumps(service_data).encode('utf8'))

        # create instances path
        instances_path = service_path + self.CONST_INSTANCES_PATH
        self.zk.ensure_path(instances_path)

        # set each instance
        for instance_item in service.instances:
            self.create_instance_path(instances_path, instance_item, service.servicename)

    def create_instance_path(self, parent_path, instance, service_name):

        if instance.id is None:
            print "instance.id is None"
            return
        instance_path = parent_path + instance.id
        # instance_data = "id: " + instance.id + \
        #                 "\nmac: " + self.check_none(instance.mac) + \
        #                 "\nmanageip: " + self.check_none(instance.manageip) + \
        #                 "\npublicip: " + self.check_none(instance.publicip) + \
        #                 "\npublicgateway: " + self.check_none(instance.publicgateway) + \
        #                 "\npublicnetmask: " + self.check_none(instance.publicnetmask) + \
        #                 "\nserviceip: " + self.check_none(instance.serviceip) + \
        #                 "\nstatus: " + self.check_none(instance.status)

        instance_data = dict(id=instance.id,
                             mac=instance.mac,
                             manageip=instance.manageip,
                             publicip=instance.publicip,
                             publicgateway=instance.publicgateway,
                             publicnetmask=instance.publicnetmask,
                             serviceip=instance.serviceip,
                             status=instance.status,
                             user=self.CONST_HOST_MAPPING[service_name]
                             )

        self.zk.ensure_path(instance_path)
        # self.zk.set(instance_path, b"" + instance_data.encode('utf8'))
        self.zk.set(instance_path, b"" + json.dumps(instance_data).encode('utf8'))
        return instance_path

    def create_usergroup_path(self, parent_path, group):
        if group is None or group.groupname is None:
            return
        group_path = parent_path + group.groupname + "/"
        # group_data = "id: " + group.id + "\ngroupname: " + \
        #              group.groupname + "\ndescription: " + self.check_none(group.description)

        group_data = dict(
                id=group.id,
                groupname=group.groupname,
                description=group.description
        )

        self.zk.ensure_path(group_path)
        self.zk.set(group_path, b"" + json.dumps(group_data).encode('utf8'))

        # create users path
        users_path = group_path + self.CONST_USERS_PATH
        self.zk.ensure_path(users_path)

        # set each user
        for user_item in group.users:
            self.create_user_path(users_path, user_item)

        # create servers path
        servers_path = group_path + self.CONST_SERVERS_PATH
        self.zk.ensure_path(servers_path)

        # set each server/host
        for server in group.servers:
            self.create_host_path(servers_path, server)

    def create_user_path(self, parent_path, user):
        if user is None or user.name is None:
            print "user is None"
            return
        user_path = parent_path + user.name + "/"
        # user_data = "id: " + user.id + "\nname: " + \
        #             user.name + "\nemail: " + self.check_none(user.email)

        user_data = dict(
                id=user.id,
                name=user.name,
                email=user.email)

        self.zk.ensure_path(user_path)
        self.zk.set(user_path, b"" + json.dumps(user_data).encode('utf8'))

        # create hosts path
        hosts_path = user_path + self.CONST_HOSTS_PATH
        self.zk.ensure_path(hosts_path)

        # set each hosts
        for host_item in user.hosts:
            self.create_host_path(hosts_path, host_item)

    def create_host_path(self, parent_path, host):
        if host is None or host.mac is None:
            return

        host_path = parent_path + host.mac

        # host_data = "ip: " + self.check_none(host.ip) + "\nmac: " + \
        #             host.mac + "\nhost_name: " + \
        #             self.check_none(host.mac) + \
        #             "\ndomain: " + self.check_none(host.domain)

        host_data = dict(
                ip=host.ip,
                mac=host.mac,
                host_name=host.host_name,
                domain=host.domain)

        self.zk.ensure_path(host_path)
        self.zk.set(host_path, b"" + json.dumps(host_data).encode('utf8'))
        return host_path

    def delete_dso_path(self):
        self.zk.delete("/dso", recursive=True)
        self.zk.ensure_path("/dso")

    def delete_account_path(self, account_id):
        account_path = self.CONST_BASE_PATH + self.CONST_ACCOUNTS_PATH + account_id
        self.zk.delete(account_path, recursive=True)

    def delete_account_mapping_path(self, account_id):

        ip2vm_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_IP2VMPATH + account_id
        ip2user_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_IP2USER_PATH + account_id
        mac2user_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_MAC2USER_PATH + account_id

        self.zk.delete(ip2vm_path, recursive=True)
        self.zk.delete(ip2user_path, recursive=True)
        self.zk.delete(mac2user_path, recursive=True)

    @staticmethod
    def check_none(data):
        return "None" if data is None else data

    def create_user2account_path(self, user2account):
        path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_USER2ACCOUNT_PATH
        self.zk.ensure_path(path)
        self.zk.set(path, b"" + json.dumps(user2account).encode('utf8'))

    def create_aid2aname_path(self, aid2aname):
        if not self.zk.exists(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH):
            self.zk.ensure_path(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH)
        path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_AID2ANAME_PATH
        self.zk.ensure_path(path)
        self.zk.set(path, b"" + json.dumps(aid2aname).encode('utf8'))

    def create_ip2user_path(self, account_info, ip2user):

        if not self.zk.exists(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH):
            self.zk.ensure_path(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH)

        ip2user_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_IP2USER_PATH
        self.zk.ensure_path(ip2user_path)

        account_path = ip2user_path + account_info.id + "/"
        self.zk.ensure_path(account_path)
        account_data = {"account_name": account_info.account_name}
        self.zk.set(account_path, b"" + json.dumps(account_data).encode('utf8'))

        for ip in ip2user.keys():
            if ip is None:
                print "Ip is None"
                continue
            ip_path = account_path + ip

            self.zk.ensure_path(ip_path)
            self.zk.set(ip_path, b"" + json.dumps(ip2user[ip]).encode('utf8'))

    def create_mac2user_path(self, account_info, mac2user):

        mac2user_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_MAC2USER_PATH
        self.zk.ensure_path(mac2user_path)

        account_path = mac2user_path + account_info.id + "/"
        self.zk.ensure_path(account_path)
        account_data = {"account_name": account_info.account_name}
        self.zk.set(account_path, b"" + json.dumps(account_data).encode('utf8'))

        for mac in mac2user.keys():
            if mac is None:
                print "mac is None"
                continue
            ip_path = account_path + mac

            self.zk.ensure_path(ip_path)
            self.zk.set(ip_path, b"" + json.dumps(mac2user[mac]).encode('utf8'))

    def gen_mapping_pre_account(self, account_info, vpn_clients):
        self.zk.ensure_path(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH)
        self.zk.ensure_path(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_IP2VMPATH)
        self.zk.ensure_path(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_MAC2USER_PATH)

        user2account = {}
        ip2user = {}
        mac2user = {}
        for group in account_info.groups:
            for user in group.users:
                user2account[user.id] = account_info.id
                for host in user.hosts:
                    user_data = dict(userid=user.id, username=user.name,
                                     useremail=user.email, groupname=group.groupname)
                    if host.ip is not None:
                        ip2user[host.ip] = user_data
                        mac2user[host.mac] = user_data

        # add vpn info
        for vpn in vpn_clients:
            vpn_user_data = dict(userid='vpn_user', username=vpn.user_name, useremail='', groupname=vpn.group)
            if vpn.ip is not None:
                vpn_ip = vpn.ip
                if vpn_ip.__contains__("/"):
                    vpn_ip = vpn_ip.split("/")[0]

                ip2user[vpn_ip] = vpn_user_data

        # create node
        self.create_ip2user_path(account_info, ip2user)

        # create node mac2user
        self.create_mac2user_path(account_info, mac2user)

        # not used now
        # self.create_user2account_path(user2account)

        # create ip2vm
        self.create_ip2vm_path(account_info)

    def gen_vm_path(self, vm_info):
        if not self.zk.exists(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH):
            self.zk.ensure_path(self.CONST_BASE_PATH + self.CONST_MAPPING_PATH)
        vms_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_VM_INFO_PATH
        self.zk.ensure_path(vms_path)
        for vm in vm_info:
            vm_node_path = vms_path + vm.manage_ip.replace('/', '-')
            vm_dict = dict(id=vm.id, type=vm.type, status=vm.status)

            self.zk.ensure_path(vm_node_path)
            self.zk.set(vm_node_path, b"" + json.dumps(vm_dict).encode('utf8'))

    def create_mapping_accounts(self, accounts):
        aid2aname = {}
        for account in accounts:
            aid2aname[account.id] = account.account_name
        self.create_aid2aname_path(aid2aname)

    def gen_services_summay(self, path, services):
        services_data = {}
        for service_item in services:
            instance_array = ""
            for instance in service_item.instances:
                instance_data = "<table class=\"table\">" \
                                "<tr>" \
                                "<td>manageip</td><td>" + self.check_none(instance.manageip) \
                                + "</td>" \
                                "</tr>" \
                                "<tr>" \
                                "<td>publicip</td><td>" + self.check_none(
                    instance.publicip) + "</td>" \
                                         "</tr>" \
                                         "<tr>" \
                                         "<td>publicgateway</td><td>" + self.check_none(
                    instance.publicgateway) + "</td>" \
                                              "</tr>" \
                                              "<tr>" \
                                              "<td>publicnetmask</td><td>" + self.check_none(
                    instance.publicnetmask) + "</td>" \
                                              "</tr>" \
                                              "<tr>" \
                                              "<td>serviceip</td><td>" + self.check_none(instance.serviceip) \
                                            + "</td>" \
                                              "</tr>" \
                                              "<tr><td>status</td><td>" + self.check_none(
                    instance.status) + "</td>" \
                                       "</tr>" \
                                            "<tr><td>user</td><td>" + \
                                self.check_none(self.CONST_HOST_MAPPING[service_item.servicename]) \
                                     + "</td>" \
                                       "</tr>" \
                                       "</table>"

                instance_array += instance_data + "\n"
            services_data[service_item.servicename] = instance_array

        self.zk.set(path, b"" + json.dumps(services_data).encode('utf8'))

    def create_ip2vm_path(self, account_info):

        base_path = self.CONST_BASE_PATH + self.CONST_MAPPING_PATH + self.CONST_IP2VMPATH
        path = base_path + account_info.id + "/"
        # self.zk.ensure_path(path)

        account_data = dict(accountname=account_info.account_name)
        self.zk.create(path, b"" + json.dumps(account_data).encode('utf8'))

        self.zk.ensure_path(path)
        for service_item in account_info.services:
            service_name = service_item.servicename
            for instance in service_item.instances:
                if instance.manageip is None:
                    continue
                manageip = instance.manageip
                if instance.manageip.__contains__('/'):
                    manageip =manageip[: manageip.find('/')]

                vm_path = path + manageip
                host_name = account_info.id + '-' + service_name

                instance_data = dict(id=instance.id,
                                     mac=instance.mac,
                                     manageip=instance.manageip,
                                     publicip=instance.publicip,
                                     publicgateway=instance.publicgateway,
                                     publicnetmask=instance.publicnetmask,
                                     serviceip=instance.serviceip,
                                     status=instance.status,
                                     servicename=service_name,
                                     hostname=host_name
                                     )
                # self.zk.ensure_path(vm_path)
                self.zk.create(vm_path, b"" + json.dumps(instance_data).encode('utf8'))

    def get_all_account(self):
        accounts_path = self.CONST_BASE_PATH + self.CONST_ACCOUNTS_PATH
        account_list = self.zk.get_children(accounts_path)
        return account_list

    def commit(self):
        self.tran.commit()


    def stopZooK(self):
        # In the end, stop it
        self.zk.stop()


if __name__ == "__main__":
    try:
        client = ZookClient()
        # client.create_accounts_path()
        account_list = client.get_all_account()
        for account in account_list:
            print account
        # print(account_list)
        print "hold"
    except Exception as exp:
        print exp.message
