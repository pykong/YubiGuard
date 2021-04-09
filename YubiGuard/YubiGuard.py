#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# YubiGuard VERSION 0.9.3
# LICENSE: GNU General Public License v3.0
# shell command for pushing ZMQ:
# echo -e $(printf '\\x01\\x00\\x%02x\\x00%s' $((1 + ${#MSG})) "$MSG")
#  | nc -q1 $IP $PORT

import argparse
import os
import re
import subprocess
import sys
import time
from multiprocessing import Process, Queue
from threading import Thread

import gi.repository
import zmq

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import AppIndicator3 as AppIndicator
from gi.repository import Gtk

# change working dir to that of script:
abspath = os.path.abspath(__file__)
d_name = os.path.dirname(abspath)
os.chdir(d_name)

# BASIC SETTINGS --------------------------------------------------------------
TIMEOUT = 5

APPINDICATOR_ID = 'yubiguard-indicator'
HELP_URL = "https://github.com/bfelder/YubiGuard#usage"

# icons:
ICON_DIR = './icons/'
OFF_ICON = ICON_DIR + 'off_icon.svg'
ON_ICON = ICON_DIR + 'on_icon.svg'
NOKEY_ICON = ICON_DIR + 'nokey_icon.svg'

# Defining signals for queue communication:
ON_SIGNAL = "ON"
OFF_SIGNAL = 'OFF'
NOKEY_SIGNAL = 'NOKEY'
EXIT_SIGNAL = 'EXIT'

URL = "tcp://{IP}:{PORT}".format(IP="127.0.0.1", PORT="5555")


# static methods:
def shell_this(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = []
    while True:
        line = p.stdout.readline().decode()
        stdout.append(line)
        # print line,
        if line == '' and p.poll() is not None:
            break
    return ''.join(stdout)


def get_scrlck_cmd():
    """
    needs screensaver to run for the session:
    """
    cmd_d = dict(
        cinammon='cinammon-screensaver-command -l',
        gnome='gnome-screensaver-command -l',
        mate='mate-screensaver-command -l',
        xfce='xflock4')
    sh_out = shell_this("ls /usr/bin/*session")

    for k, v in cmd_d.iteritems():
        if k in sh_out:
            return v


class PanelIndicator(object):
    def __init__(self, pi_q, on_q):
        self.indicator = AppIndicator.Indicator.new(
            APPINDICATOR_ID, os.path.abspath(NOKEY_ICON),
            AppIndicator.IndicatorCategory.SYSTEM_SERVICES)

        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu)

        self.pi_q = pi_q
        self.on_q = on_q

    def run_pi(self):
        # suppresses error: Couldn't connect to accessibility bus:
        # Failed to connect to socket:
        shell_this("export NO_AT_BRIDGE=1")

        # listener loop for icon switch signals
        ui_thread = Thread(target=self.update_icon)
        ui_thread.daemon = True
        ui_thread.start()

        # starting Gtk main:
        Gtk.main()

    @property
    def build_menu(self):
        menu = Gtk.Menu()

        item_unlock = Gtk.MenuItem(label='Unlock')
        item_unlock.connect('activate', self.unlock)
        menu.append(item_unlock)
        self.item_unlock = item_unlock
        self.item_unlock.set_sensitive(False)  # default state

        item_help = Gtk.MenuItem(label='Help')
        item_help.connect('activate', self.open_help)
        menu.append(item_help)

        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)

        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def unlock(self, *args):
        self.on_q.put(ON_SIGNAL)

    def open_help(self, *arg):
        help_cmd = "xdg-open {HELP_URL} || " \
                   "gnome-open {HELP_URL} || " \
                   "kde-open {HELP_URL} || " \
                   "notify-send --expire-time=7000" \
                   """ \"Could not open YubiGuard web help:\" \
                   \"{HELP_URL}\"""".format(HELP_URL=HELP_URL)

        shell_this(help_cmd)

    def quit(self, *arg):
        print('Quitting Gtk.')
        Gtk.main_quit()

    def update_icon(self):
        while True:
            if self.pi_q.qsize() > 0:
                state = self.pi_q.get()

                if state == ON_SIGNAL:
                    self.indicator.set_icon_full(os.path.abspath(ON_ICON), "")
                    # activate unlock button
                    self.item_unlock.set_sensitive(False)
                elif state == OFF_SIGNAL:
                    self.indicator.set_icon_full(os.path.abspath(OFF_ICON), "")
                    # deactivate unlock button
                    self.item_unlock.set_sensitive(True)
                elif state == NOKEY_SIGNAL:
                    self.indicator.set_icon_full(
                        os.path.abspath(NOKEY_ICON), "")
                    # deactivate unlock button
                    self.item_unlock.set_sensitive(False)

            time.sleep(.1)


class ZmqListener(object):
    def __init__(self, on_q):
        """ Listens for triggering through zmq message."""
        self.on_q = on_q
        ctx = zmq.Context.instance()
        self.s = ctx.socket(zmq.PULL)
        self.s.bind(URL)

    def start_listener(self):
        print('ZMQ listener started')
        while True:
            try:
                self.s.recv(zmq.NOBLOCK)  # note NOBLOCK here
            except zmq.Again:
                # no message to recv, do other things
                time.sleep(0.05)
            else:
                self.on_q.put(ON_SIGNAL)


class AsynchronousFileReader(Thread):
    """
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    Credits for this class goes to Stefaan Lippens:
    http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading
    """

    def __init__(self, fd, queue):
        assert callable(fd.readline)
        Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        """ The body of the tread: read lines and put them on the queue."""
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    @property
    def eof(self):
        """ Check whether there is no more content to expect."""
        return not self.is_alive() and self._queue.qsize() > 0


class YubiGuard:
    def __init__(self, scrlck_mode=False):
        self.scrlck_mode = scrlck_mode

        self.id_q = Queue()
        self.on_q = Queue()
        self.pi_q = Queue()

        # init processes
        gi_proc = Process(target=self.get_ids)
        gi_proc.daemon = True

        cs_proc = Process(target=self.change_state)
        # no daemon, or main program will terminate before Keys can be unlocked
        cs_proc.daemon = False

        zmq_lis = ZmqListener(
            self.on_q)  # somehow works ony with threads not processes
        zmq_lis_thr = Thread(target=zmq_lis.start_listener)
        zmq_lis_thr.setDaemon(True)

        pi = PanelIndicator(self.pi_q, self.on_q)

        # starting processes and catching exceptions:
        try:
            gi_proc.start()
            cs_proc.start()
            zmq_lis_thr.start()

            pi.run_pi()  # main loop of root process

        except (KeyboardInterrupt, SystemExit):
            print('Caught exit event.')

        finally:
            # send exit signal, will reactivate YubiKey slots
            print('Sending EXIT_SIGNAL')
            self.on_q.put(EXIT_SIGNAL)

    def get_ids(self):
        old_id_l = []
        no_key = True
        pat = re.compile(r"(?:Yubikey.*?id=)(\d+)", re.IGNORECASE)
        while True:
            new_id_l = []
            # get list of xinput device ids and extract those of YubiKeys:

            xinput = shell_this('xinput list')
            matches = re.findall(pat, xinput)
            new_id_l.extend(matches)
            new_id_l.sort()

            if not new_id_l and not no_key:
                self.pi_q.put(NOKEY_SIGNAL)
                print('No YubiKey(s) detected.')
                no_key = True
            elif new_id_l and no_key:
                self.pi_q.put(OFF_SIGNAL)
                print('YubiKey(s) detected.')
                no_key = False
                # notify:
                msg_cmd = """notify-send --expire-time=2000 \
                'YubiKey(s) detected.'"""
                shell_this(msg_cmd)

            if new_id_l != old_id_l:
                print('Change in YubiKey ids detected. From {} to {}.'.format(
                    old_id_l, new_id_l))
                self.id_q.put(new_id_l)

                # lock screen if screenlock and YubiKey is removed:
                if self.scrlck_mode and len(new_id_l) < len(old_id_l):
                    print('Locking screen.')
                    shell_this(get_scrlck_cmd())  # execute screen lock command

            old_id_l = new_id_l

            time.sleep(.1)

    def turn_keys(self, id_l, lock=True
                  ):  # problem of value loss of cs_id_l found in this function
        tk_id_l = id_l
        if lock:
            print('Locking YubiKey(s).')
            state_flag = '0'
            self.pi_q.put(OFF_SIGNAL)
        else:
            print('Unlocking YubiKey(s).')
            state_flag = '1'
            self.pi_q.put(ON_SIGNAL)

        shell_this('; '.join(["xinput set-int-prop {} \"Device Enabled\" 8 {}".
                              format(tk_id, state_flag) for tk_id in tk_id_l]))

    def check_state(self, check_id_l):
        # check if all states have indeed changed:
        pat = re.compile(r"(?:Device Enabled.+?:).?([01])", re.IGNORECASE)
        # check if state has indeed changed:

        for tk_id in check_id_l:
            sh_out = shell_this('xinput list-props {}'.format(tk_id))
            match = re.search(pat, sh_out)
            if match:
                if match.group(1) != '0':
                    return False

    def change_state(self):
        cs_id_l = []
        cs_signal = ''

        while True:
            # retrieve input from queues
            while self.id_q.qsize() > 0:
                cs_id_l = self.id_q.get()

            while self.on_q.qsize() > 0:
                cs_signal = self.on_q.get()
                # not accepting any more signals
                if cs_signal == EXIT_SIGNAL:
                    self.turn_keys(cs_id_l, lock=False)
                    sys.exit(0)

            # lock/unlock
            if cs_id_l:
                if cs_signal == ON_SIGNAL:
                    self.turn_keys(cs_id_l, lock=False)

                    mon_thread = Thread(
                        target=self.yk_monitor, args=(cs_id_l, ))
                    mon_thread.start()
                    mon_thread.join()

                    # putting in separator, nullifying all preceding ON_SIGNALS
                    # to prevent possible over-triggering:
                    self.on_q.put('')

                elif self.check_state(
                        cs_id_l) is False:  # lock keys if they are unlocked
                    self.turn_keys(cs_id_l, lock=True)
            # reset state to prevent continued unlocking/locking
            cs_signal = ''
            time.sleep(.01)

    def yk_monitor(self, mon_l):
        # forming command to run parallel monitoring processes
        mon_cmd = ' & '.join(["xinput test {}".format(y_id) for y_id in mon_l])
        monitor = subprocess.Popen(mon_cmd, shell=True, stdout=subprocess.PIPE)

        stdout_queue = Queue()
        stdout_reader = AsynchronousFileReader(monitor.stdout, stdout_queue)
        stdout_reader.start()

        triggered = False
        timestamp = time.time()
        while not stdout_reader.eof and time.time() - timestamp < TIMEOUT:
            while stdout_queue.qsize() > 0:
                stdout_queue.get()  # emptying queue
                triggered = True
                time.sleep(.04)
            if triggered:
                print('YubiKey triggered. Now disabling.')
                break

            time.sleep(.001)
        if not triggered:
            print('No YubiKey triggered. Timeout.')

# FIRING UP YUBIGUARD ---------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YubiGuard help')
    parser.add_argument(
        '-t', nargs='?', default="", help='activates YubiGuard.py as trigger')
    parser.add_argument(
        '-l',
        nargs='?',
        default="",
        help='lock screen if any YubiKey is removed')
    args = parser.parse_args()

    if args.t is None:
        print("Sending ON_SIGNAL.")
        context = zmq.Context()
        zmq_socket = context.socket(zmq.PUSH)
        zmq_socket.connect(URL)
        zmq_socket.send(ON_SIGNAL)

    elif args.l is None:
        print("Starting YubiGuard in screen lock mode.")
        yg = YubiGuard(scrlck_mode=True)
    else:
        print("Starting YubiGuard.")
        yg = YubiGuard()
