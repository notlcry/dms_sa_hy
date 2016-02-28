# coding: utf-8
__author__ = 'huiyu'

from datetime import datetime
import time
from swagger_client.apis import account_api
from swagger_client.apis import vpnclient_api
from zooClient import zk_client
import logging
import traceback


class InventorySync:

    def __init__(self):
        logging.basicConfig()

    def account_sync(self, account_id, zookeeper_host):
        try:
            dso_account_client = account_api.AccountApi()
            dso_vpn_client = vpnclient_api.VpnclientApi()

            account_info = dso_account_client.accounts_account_id_get(account_id)

            # get 1000 for now, FIXME
            vpn_info = dso_vpn_client.vpn_account_id_get(account_id, 1, 1000)
            vpn_clients = vpn_info.results.item

            start_sync_zoo = datetime.now()
            client = zk_client.ZookClient(zookeeper_host)

            client.delete_account_path(account_id)
            client.create_account_path(account_info)
            client.create_accountinfo_path(account_info)

            client.delete_account_mapping_path(account_id)
            client.gen_mapping_pre_account(account_info, vpn_clients)

            client.commit()
            client.stopZooK()
            end_sync_zoo = datetime.now()
            print "sync zookeeper use: "
            print (end_sync_zoo - start_sync_zoo)
        except Exception as exp:
            print exp.message
            traceback.print_exc()


if __name__ == "__main__":
    start = time.time()
    sync = InventorySync()
    sync.account_sync('a6d0944d-a1e1-4a55-9ae8-9559dc88e00f', 'localhost:2181')
    used = time.time() - start
    print "sync finish, use %d sec " % used