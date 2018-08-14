from collections import defaultdict

from voltdbclient import *


class VoltExecutor(object):
    def __init__(self, server, port, user, password, query_timeout):
        self.client = None
        self.parameters = {"host": server, "port": port, "procedure_timeout": query_timeout}
        if user:
            self.parameters["username"] = user
        if password:
            self.parameters["password"] = password

        self.init_client()

    def init_client(self):
        try:
            self.client = FastSerializer(**self.parameters)
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
            # no connection, set client to None so it can be lazy reinitialized next time we invoke
            self.client = None
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
        if not self.check_client_alive():
            return []
        proc = VoltProcedure(self.client, "@SystemCatalog", [FastSerializer.VOLTTYPE_STRING])
        response = proc.call(["functions"])
        if response.status == -1:
            # no connection, set client to None so it can be lazy reinitialized next time we invoke
            self.client = None
            return []
        if response.status != 1:
            # failure
            return []
        table = response.tables[0]
        if len(table.tuples) == 0:
            # no data
            return []
        result = []
        for row in table.tuples:
            result.append(row[1])
        return result

    def get_procedure_catalog(self):
        if not self.check_client_alive():
            return []
        proc = VoltProcedure(self.client, "@SystemCatalog", [FastSerializer.VOLTTYPE_STRING])
        response = proc.call(["procedures"])
        if response.status == -1:
            # no connection, set client to None so it can be lazy reinitialized next time we invoke
            self.client = None
            return []
        if response.status != 1:
            # failure
            return []
        table = response.tables[0]
        if len(table.tuples) == 0:
            # no data
            return []
        result = []
        for row in table.tuples:
            result.append(row[2])
        return result
