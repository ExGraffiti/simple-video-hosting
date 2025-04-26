# -*- coding: utf-8 -*-
import cfg
import mysql
from mysql.connector import connect, Error


class Storage:
    def __init__(self):
        self.connection = None
        self.init_db()

    def __del__(self):
        self.close()

    def init_db(self):
        try:
            self.connection = mysql.connector.connect(
                user=cfg.db['user'],
                password=cfg.db['password'],
                host=cfg.db['host'],
                port=cfg.db['port'],
                database=cfg.db['database'])
        except Error as err:
            print(err)

    def get_cursor(self):
        try:
            self.connection.ping(reconnect=True, attempts=3, delay=5)
        except Error as err:
            print(err)
            self.init_db()
        return self.connection.cursor()

    def close(self):
        self.connection.close()


