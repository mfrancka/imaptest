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

class imap_test(threading.Thread):
        def __init__(self, login, passwd, server):
                threading.Thread.__init__(self)
                self.login = login
                self.passwd = passwd
                self.server = server
        def run(self):
                global running
                lock = threading.Lock()
                try:
                        M = imaplib.IMAP4_SSL(self.server)
                        self.sleep()
                        M.login(self.login, self.passwd)
                        print 'logged in:\t {}'.format(self.login)
                except:
                        lock.acquire()
                        print 'Login failed for {}.'.format(self.login)
                        lock.release()
                        sys.exit(1)
                else:
                        M.select()
                        while running:
                                typ, data = M.list()
                                self.sleep()
                        lock.acquire()
                        print 'Stopping:\t {}'.format(self.login)
                        lock.release()
                        M.close()
                        M.logout()
        def sleep(self):
                time.sleep(random.randint(1,3))

def read_logins(loginfile):
        logins = []
        try:
                with open(loginfile, 'r') as f:
                        reader = csv.reader(f, delimiter=':')
                        for row in reader:
                                logins.append(row)
                return logins
        except:
                print 'Error reading {}'.format(loginfile)
                raise
                sys.exit()

def sighandler(num, stack):
        print 'Ctrl+C pressed...'
        global running
        running = False

def main(argv):
        loginfile = 'logins.txt'
        threads = []
        try:
                opts, args = getopt.getopt(argv, '-l:')
        except getopt.GetoptError:
                print 'imaptest.py -l <login file>'
                sys.exit()
        for opt, arg in opts:
                if opt == '-l':
                        loginfile = arg
        logins = read_logins(loginfile)
        for credential in logins:
                try:
                        threadx = imap_test(credential[0], credential[1], credential[2])
                        threadx.start()
                        threads.append(threadx)
                except Exception, errtxt:
                        print errtxt
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
