def enum(**enums):
    return type('Enum', (), enums)

Tenant_Sate = enum(INIT="init",PACKAGE_ACTIVATE="service_activing",VM_CREATE="vm_creating",MONITOR_CPE= "monitor_cpe",SA_PROVISION="sa_provision",PACKAGE_TIMEOUT="package_timeout",FINISH="finish")


avro_schema = """
    {"namespace": "com.dadycloud.sa",
    "type": "record",
    "name": "event",
    "fields": [
                 {"name": "timestamp", "type": "long"},
                 {"name": "src",       "type": "string"},
                 {"name": "host_ip",   "type": "string"},
                 {"name": "rawdata",   "type": "bytes"}
            ]
            }
         """