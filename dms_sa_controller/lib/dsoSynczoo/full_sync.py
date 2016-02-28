# coding: utf-8
__author__ = 'huiyu'

from datetime import datetime
import time
from swagger_client.apis import account_api
from swagger_client.apis import vpnclient_api
from zooClient import zk_client
from swagger_client.apis import vm_api
import traceback


def full_sync():
    try:
        dso_account_client = account_api.AccountApi()
        dso_vpn_client = vpnclient_api.VpnclientApi()
        dso_vm_client = vm_api.VmApi()

        # get 1 page count 100 for now, must for page request long term
        rtn = dso_account_client.accounts_get(1, 500)
        accounts = rtn.results.item

        # client = zk_client.ZookClient("localhost:2181")
        # client.create_mapping_accounts(accounts.item)

        account_info_map = {}
        vpn_client_map = {}
        # get account info for pre account
        for account in accounts:
            account_info = dso_account_client.accounts_account_id_get(account.id)
            vpn_info = dso_vpn_client.vpn_account_id_get(account.id, 1, 1000)
            vpn_clients = vpn_info.results.item

            # client.create_accountinfo_path(account_info)
            account_info_map[account.id] = account_info
            vpn_client_map[account.id] = vpn_clients

            # client.gen_mapping_pre_account(account_info, vpn_clients)

            # vm_info = dso_vm_client.vm_account_id_get(account.id)
            # client.gen_vm_path(vm_info)

        start_sync_zoo = datetime.now()
        client = zk_client.ZookClient("10.74.113.102:2181")
        # client = zk_client.ZookClient("localhost:2181")
        client.delete_dso_path()
        client.create_accounts_path(accounts)

        for account in accounts:
            client.create_accountinfo_path(account_info_map[account.id])
            client.gen_mapping_pre_account(account_info_map[account.id], vpn_client_map[account.id])

        client.commit()
        client.stopZooK()
        end_sync_zoo = datetime.now()
        print "sync zookeeper use: "
        print (end_sync_zoo - start_sync_zoo)
    except Exception as exp:
        print exp.message
        traceback.print_exc()


if __name__ == "__main__":
    while True:
        start = time.time()
        full_sync()
        used = time.time() - start
        print "full sync finish, use %d sec " % used
        time.sleep(60)
