# coding: utf-8
__author__ = 'huiyu'

from datetime import datetime
import time
from swagger_client.apis import account_api
from swagger_client.apis import vpnclient_api
from zooClient import zk_client_tran
import logging
import traceback
import sys
import sync_redis


def account_sync(account_id, zookeeper_host, is_sync_redis=False):
        try:
            dso_account_client = account_api.AccountApi()
            dso_vpn_client = vpnclient_api.VpnclientApi()

            account_info = dso_account_client.accounts_account_id_get(account_id)

            # get 1000 for now, FIXME
            vpn_info = dso_vpn_client.vpn_account_id_get(account_id, 1, 1000)
            vpn_clients = vpn_info.results.item

            start_sync_zoo = datetime.now()
            client = zk_client_tran.ZookClient(zookeeper_host)

            client.delete_account_path(account_id)
            client.create_account_path(account_info)
            client.create_accountinfo_path(account_info)

            client.sync_mapping_pre_account(account_info, vpn_clients)

            client.commit()
            client.stopZooK()
            end_sync_zoo = datetime.now()
            print "sync zookeeper use: "
            print (end_sync_zoo - start_sync_zoo)

            # add sync 2 redis
            sync_redis.sync_to_redis(account_info, vpn_clients)
        except Exception as exp:
            print exp.message
            traceback.print_exc()


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "pls enter accountid and zookeeper host"
        print "usage: python account_sync_tran.py accountID localhost:2181"
        exit(0)
    account_id = sys.argv[1]
    zookeeper_host = sys.argv[2]
    start = time.time()
    account_sync(account_id, zookeeper_host)
    used = time.time() - start
    print "sync finish, use %d sec " % used
