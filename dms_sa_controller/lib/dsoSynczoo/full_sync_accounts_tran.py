# coding: utf-8
__author__ = 'huiyu'

import time
from swagger_client.apis import account_api
import account_sync_tran
import clear_account
import traceback
import sys


def full_sync(zookeeper_host, is_sync_redis=False):
    try:
        dso_account_client = account_api.AccountApi()

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
                account_sync_tran.account_sync(account.id, zookeeper_host, is_sync_redis)
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
        print "usage: python full_sync_accounts_tran.py localhost:2181"
        exit(0)

    zookeeper_host = sys.argv[1]

    while True:
        start = time.time()
        full_sync(zookeeper_host)
        used = time.time() - start
        print "full sync %s finish, use %d sec " % (zookeeper_host, used)
        time.sleep(60)
