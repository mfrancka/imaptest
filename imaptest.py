#!/usr/bin/env python

'''
        imaptest.py

        Simple IMAP client simulator

        Copyright (C) 2014 Eduardo Ramos <eduardo@freedominterface.org>

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import imaplib, getopt
import random, time, threading
import csv, sys, signal


class timer:
    def __init__(self):
        self.start_time = 0

    def start(self):
        self.start_time = time.perf_counter()

    def end(self):
        self.counted_time = time.perf_counter() - self.start_time
        return self.counted_time


class imap_test(threading.Thread):
        def __init__(self, login, passwd, server):
                threading.Thread.__init__(self)
                self.login = login
                self.passwd = passwd
                self.server = server

        def run(self):
                global running
                counter = timer()
                lock = threading.Lock()
                try:
                        M = imaplib.IMAP4_SSL(self.server)
                        self.sleep()
                        counter.start()
                        M.login(self.login, self.passwd)
                        lock.acquire()
                        counter.end()
                        lock.release()
                        print('logged in:\t {} in {}s'.
                              format(self.login, counter.counted_time))
                except Exception as e:
                        lock.acquire()
                        print('Login failed for {}.'.format(self.login))
                        print(e)
                        lock.release()
                        sys.exit(1)
                else:
                        M.select()
                        while running:
                            counter.start()
                            typ, data = M.list()
                            print(counter.end())
                            self.sleep()
                        lock.acquire()
                        print('Stopping:\t {}'.format(self.login))
                        lock.release()
                        M.logout()

        def sleep(self):
                time.sleep(random.randint(1, 3))


def read_logins(loginfile, master_password=None, master_server=None):
        logins = []
        try:
                with open(loginfile, 'r') as f:
                        reader = csv.reader(f, delimiter=':')
                        for row in reader:
                            if master_password:
                                if len(row) >= 2:
                                    row[1] = master_password
                                else:
                                    row.append(master_password)
                            if master_server:
                                if len(row) >= 3:
                                    row[2] = master_server
                                else:
                                    row.append(master_server)
                            logins.append(row)
                return logins
        except:
                print('Error reading {}'.format(loginfile))
                raise
                sys.exit()


def sighandler(num, stack):
        print('Ctrl+C pressed...')
        global running
        running = False


def help():
    print('imaptest.py -l <login file> [-p <master_password>] '
          '[-s <master_server>] [-n <number_of_users_from_file>]')


def main(argv):
        loginfile = 'logins.txt'
        master_password = None
        master_server = None
        max_users = 0
        threads = []
        if not argv:
            help()
            sys.exit()
        try:
            opts, args = getopt.getopt(argv, 'l:p:s:n:')
        except getopt.GetoptError:
                help()
                sys.exit()
        for opt, arg in opts:
                if opt == '-l':
                        loginfile = arg
                if opt == '-p':
                    print('Using master password for logins.')
                    master_password = arg
                if opt == '-s':
                    master_server = arg
                    print('Using master server for logins: {}'
                          .format(master_server))
                if opt == '-n':
                    max_users = int(arg)
                    print('Use {} users'.format(max_users))
        logins = read_logins(loginfile, master_password, master_server)
        if max_users == 0:
            max_users = len(logins)
        for credential in logins[:max_users]:
                try:
                        threadx = imap_test(credential[0], credential[1],
                                            credential[2])
                        threadx.start()
                        threads.append(threadx)
                except Exception as errtxt:
                        print(errtxt)
        while True:
                if not any([thread.isAlive() for thread in threads]):
                        break
                else:
                        time.sleep(1)

if __name__ == '__main__':
        signal.signal(signal.SIGINT, sighandler)
        signal.signal(signal.SIGTERM, sighandler)
        running = True
        main(sys.argv[1:])
