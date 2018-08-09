from collections import defaultdict

from voltdbclient import *
import time


class VoltExecuter(object):
    def __init__(self):
        self.client = None
        self.init_client()

    def init_client(self):
        try:
            self.client = FastSerializer("localhost", 21212)
        except:
            self.client = None

    def check_client_alive(self):
        if self.client is None:
            self.init_client()
            if self.client is None:
                return False
        return True

    def get_table_catalog(self):
        if not self.check_client_alive():
            return dict()
        proc = VoltProcedure(self.client, "@SystemCatalog", [FastSerializer.VOLTTYPE_STRING])
        response = proc.call(["columns"])
        if response.status == -1:
            # no connection try to reinitialize the client
            self.init_client()
            return dict()
        if response.status != 1:
            # failure
            return dict()
        table = response.tables[0]
        if len(table.tuples) == 0:
            # no data
            return dict()
        result = defaultdict(list)
        for row in table.tuples:
            table_name, column_name = row[2], row[3]
            result[table_name].append(column_name)
        return result

    # TODO: currently consider view same as table, so leave it blank
    def get_view_catalog(self):
        return []

    def get_function_catalog(self):
        # return a list of function names
        return []

    def get_procedure_catalog(self):
        # return a list of procedure names
        return []



ve = VoltExecuter()

ve.get_table_catalog()
# time.sleep(5)
# ve.get_table_catalog()
# time.sleep(5)
# ve.get_table_catalog()
