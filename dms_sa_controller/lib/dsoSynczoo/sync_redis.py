from ..utils import logger
from sync_kafka_client import InventoryKafkaClient as client


def sync_to_redis(account_info, vpn_clients):
    logger.info("start sync dso info to redis, " + account_info.id)
    account_id = account_info.id

    # account
    client.send_create(
        account_id, "account", account_info.to_kafka)

    # sync each group
    for group in account_info.groups:
        client.send_create(account_id, "usergroup", group.to_kafka)
        for user in group.users:
            client.send_create(account_id, "user", user.to_kafka(group))
            for host in user.hosts:
                client.send_create(account_id, "host", host.to_kafka_user_host(user))

        for server in group.servers:
            client.send_create(account_id, "host", server.to_kafka_group_host(group))

    # sync vpn
    for vpn in vpn_clients:
        client.send_create(account_id, "vpn", vpn.to_kafka)
