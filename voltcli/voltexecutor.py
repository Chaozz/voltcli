from collections import defaultdict

from voltdbclient import *


class VoltExecutor(object):
    def __init__(self, server, port, user, password, query_timeout, kerberos, ssl, ssl_set, credentials):
        self.client = None
        self.parameters = {"host": server, "port": port, "procedure_timeout": query_timeout}
        if user:
            self.parameters["username"] = user
        if password:
            self.parameters["password"] = password

        if credentials:
            # if credential file is specified, parse it as username/password
            try:
                with open(credentials, "r") as credentialsFile:
                    content = ""
                    for line in credentialsFile:
                        content += line
                    _, usr, _, pswd = content.replace(':', ' ').split()
                    self.parameters["username"] = usr
                    self.parameters["password"] = pswd
            except IOError:
                print("Credentials file not found or permission denied.")

        if kerberos:
            # use kerberos auth
            # more notes:
            # you must first make sure you have the python-gssapi package installed.
            # Then, login to your Kerberos account using kinit before invoking the Python client.
            self.parameters["kerberos"] = True

        if ssl or ssl_set:
            self.parameters["usessl"] = True

        if ssl_set:
            self.parameters["ssl_config_file"] = ssl_set

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
        return dict()

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
