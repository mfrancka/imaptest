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


class statistics:
    def __init__(self):
        pass


class timer:
    def __init__(self):
        self.start_time = 0

    def start(self):
        self.start_time = time.perf_counter()

    def end(self):
        self.counted_time = time.perf_counter() - self.start_time
        return self.counted_time


class imap_test(threading.Thread):
        def __init__(self, login, passwd, server, number):
                threading.Thread.__init__(self)
                self.login = login
                self.passwd = passwd
                self.server = server
                self.number = number

        def run(self):
                global running
                global stats
                counter = timer()
                lock = threading.Lock()
                try:
                        M = imaplib.IMAP4_SSL(self.server)
                        self.sleep()
                        counter.start()
                        M.login(self.login, self.passwd)
                        counter.end()
                        stats[self.number] = {'login_time':
                                              counter.counted_time}
                        stats[self.number]['address'] = self.login
                        print('[{}]logged in:\t {} in {}s'.
                              format(self.number, self.login,
                                     counter.counted_time))
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
                            counter.end()
                            stats[self.number]['select_time'] =\
                                counter.counted_time
                            self.sleep()
                        lock.acquire()
                        print('Stopping:\t {}'.format(self.login))
                        lock.release()
                        counter.start()
                        M.logout()
                        counter.end()
                        stats[self.number]['logout_time'] =\
                            counter.counted_time

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
        global stats
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
        thread_number = 0
        for credential in logins[:max_users]:
                try:
                        threadx = imap_test(credential[0], credential[1],
                                            credential[2], thread_number)
                        threadx.start()
                        threads.append(threadx)
                        thread_number += 1
                except Exception as errtxt:
                        print(errtxt)
        while True:
                if not any([thread.isAlive() for thread in threads]):
                        break
                else:
                    print('connected: {}'.format(len(stats)))
                    time.sleep(1)
        statistics = showstats(stats)
        statistics.show_long_times()


class showstats:
    def __init__(self, stats):
        self.stats = stats

    def show(self):
        for i in self.stats.keys():
            print(self.stats[i])

    def show_long_times(self):
        counter = 0
        for i in self.stats.keys():
            if self.stats[i]['login_time'] > 1:
                print(self.stats[i])
            else:
                counter += 1
        print('Hide {} results'.format(counter))

if __name__ == '__main__':
        signal.signal(signal.SIGINT, sighandler)
        signal.signal(signal.SIGTERM, sighandler)
        running = True
        stats = {}
        main(sys.argv[1:])
