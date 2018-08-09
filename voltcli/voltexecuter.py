from voltdbclient import *


class VoltExecuter(object):
    def __init__(self):
        self.client = FastSerializer("localhost", 21212)

    def get_table_catalog(self):
        proc = VoltProcedure(self.client, "@SystemCatalog", [FastSerializer.VOLTTYPE_STRING])
        response = proc.call(["columns"])
        print(response.status)
        for t in response.tables:
            print(t)
        # print(proc.call(["columns"]).tables)



ve = VoltExecuter()

ve.get_table_catalog()
