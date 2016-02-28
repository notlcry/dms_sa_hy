# coding: utf-8
__author__ = 'huiyu'

from datetime import datetime
import time
from swagger_client.apis import account_api
from swagger_client.apis import vpnclient_api
from zooClient import zk_client
import logging
import traceback


class InventoryClear:

    def __init__(self):
        logging.basicConfig()

    def clear(self, current_list, zookeeper_host):
        try:

            client = zk_client.ZookClient(zookeeper_host)
            zoo_account_list = client.get_all_account()
            for zoo_account in zoo_account_list:
                if not current_list.__contains__(zoo_account):
                    print "account " + zoo_account + "is not used, will be cleared."
                    client.delete_account_path(zoo_account)
                    client.delete_account_mapping_path(zoo_account)

            client.stopZooK()
        except Exception as exp:
            print exp.message
            traceback.print_exc()


if __name__ == "__main__":
    start = time.time()
    sync = InventoryClear()
    sync.clear(['a6d0944d-a1e1-4a55-9ae8-9559dc88e00f'], 'localhost:2181')
    used = time.time() - start
    print "clear finish, use %d sec " % used
