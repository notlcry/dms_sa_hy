# coding: utf-8
__author__ = 'huiyu'

from datetime import datetime
import time
from swagger_client.apis import account_api
from swagger_client.apis import vpnclient_api
from zooClient import zk_client
from swagger_client.apis import vm_api
import account_sync
import clear_account
import traceback
import sys


def full_sync(zookeeper_host):
    try:
        dso_account_client = account_api.AccountApi()
        sync_pre = account_sync.InventorySync()

        current_account_list = []
        current_page = 1
        size = 10
        # get one page count 10 for once,
        rtn = dso_account_client.accounts_get(current_page, size)
        accounts = rtn.results.item
        pages = rtn.total

        while current_page <= pages:
            # get account info for pre account
            for account in accounts:
                current_account_list.append(account.id)
                sync_pre.account_sync(account.id, zookeeper_host)
            current_page += 1
            rtn = dso_account_client.accounts_get(current_page, size)
            accounts = rtn.results.item
            pages = rtn.total

        clear_client = clear_account.InventoryClear()
        clear_client.clear(current_account_list, zookeeper_host)

    except Exception as exp:
        print exp.message
        traceback.print_exc()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "pls enter zookeeper host"
        exit(0)

    zookeeper_host = sys.argv[1]

    while True:
        start = time.time()
        full_sync(zookeeper_host)
        used = time.time() - start
        print "full sync %s finish, use %d sec " % (zookeeper_host, used)
        time.sleep(60)
