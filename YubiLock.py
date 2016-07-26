#!/usr/bin/env python
# -*- coding: utf-8 -*-
# YubiLock VERSION 0.4
# LICENSE: GNU General Public License v3.0
# https://stackoverflow.com/questions/285716/trapping-second-keyboard-input-in-ubuntu-linux
#
# trigger with following shell command:
# echo -e $(printf '\\x01\\x00\\x%02x\\x00%s' $((1 + ${#m})) "ENABLE") | nc -q1 localhost 5555

import os
import subprocess
import shlex
import re
import time
import threading
import Queue
import zmq
import sys


# change working dir to that of script:
abspath = os.path.abspath(__file__)
d_name = os.path.dirname(abspath)
os.chdir(d_name)


# static methods:
def shell(cmd):
    shlex_cmd = shlex.split(cmd)
    stdout = subprocess.Popen(shlex_cmd, stdout=subprocess.PIPE)
    return stdout


def notify(icon=''):
    msg_cmd = "notify-send --expire-time=2000 " \
              "--icon={ICON} ' '".format(ICON=icon)
    shell(msg_cmd)


class AsynchronousFileReader(threading.Thread):
    """
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    Credits for this class goes to Stefaan Lippens:
    http://stefaanlippens.net/python-asynchronous-subprocess-pipe-reading
    """

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        """ The body of the tread: read lines and put them on the queue."""
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    @property
    def eof(self):
        """ Check whether there is no more content to expect."""
        return not self.is_alive() and self._queue.empty()


class YubiLock:
    def __init__(self):
        self.yubi_id_l = []
        self.running = True  # keeps while loops alive
        self.active = False  # ON/OFF master flag
        self.timeout = 2  # timeout in seconds

        self.lock = threading.Lock()

        # icons:
        self.on_icon = os.path.abspath("./icons/on_icon.svg")
        self.off_icon = os.path.abspath("./icons/off_icon.svg")

        # starting threads and catching exceptions:
        gi_thread = threading.Thread(target=self.get_ids)
        cs_thread = threading.Thread(target=self.change_state)

        try:
            gi_thread.start()
            cs_thread.start()

            # setting listening for input as main loop
            self.listener()

        except (KeyboardInterrupt, SystemExit):
            self.cleanup()
        finally:
            gi_thread.join()
            cs_thread.join()
            sys.exit(0)

    def get_ids(self):
        gi_l = []  # local list of this method
        while self.running:
            with self.lock:
                del gi_l[:]  # emptying list

                pat = re.compile(r"(?:Yubikey.*?id=)(\d+)", re.IGNORECASE)

                list_cmd = 'xinput list'
                xinput = shell(list_cmd)

                for line in xinput.stdout:
                    match = re.search(pat, line)
                    if match:
                        yubi_id = match.groups()
                        gi_l.extend(yubi_id)

                self.yubi_id_l = gi_l  # making available to class

            time.sleep(.1)

    def switch(self, state, id_l):
        print 'switch - id_l: ', id_l
        cmd_arg = ""
        if state == 'ON':
            cmd_arg = "--enable"
            on_msg = "YubiKey(s) enabled."
            print(on_msg)
            notify(self.on_icon)
        elif state == 'OFF':
            cmd_arg = "--disable"
            off_msg = "YubiKey(s) disabled."
            print(off_msg)
            notify(self.off_icon)

        for id_item in id_l:
            on_cmd = "xinput {} {}".format(cmd_arg, id_item)
            shell(on_cmd)

    def change_state(self):
        lock = False
        while self.running:
            with self.lock:
                if self.yubi_id_l:
                    if self.active:
                        self.switch('ON', self.yubi_id_l)
                        mon_thread = threading.Thread(target=self.yubikey_monitor, args=(self.yubi_id_l,))
                        mon_thread.start()
                        mon_thread.join()
                        lock = False
                    elif not self.active and not lock:
                        self.switch('OFF', self.yubi_id_l)
                        lock = True

            time.sleep(.01)

    def yubikey_monitor(self, mon_l):
        # forming command to run parallel monitoring processes
        mon_cmd = "xinput test {}"
        multi_mon_cmd = ' & '.join([mon_cmd.format(y_id) for y_id in mon_l])

        monitor = shell(multi_mon_cmd)

        # Launch the asynchronous readers of the process' stdout and stderr.
        stdout_queue = Queue.Queue()
        stdout_reader = AsynchronousFileReader(monitor.stdout, stdout_queue)
        stdout_reader.start()

        triggered = False
        timestamp = time.time()
        while not stdout_reader.eof and time.time() - timestamp < self.timeout:
            while not stdout_queue.empty():
                stdout_queue.get()  # emptying queue
                triggered = True
                time.sleep(.01)
            if triggered:
                print('Yubikey triggered. Now disabling.')
                break

            time.sleep(.01)

        monitor.kill()
        stdout_reader.join()
        self.active = False

    def listener(self):
        """ Listens for triggering through zmq message."""
        ctx = zmq.Context.instance()
        s = ctx.socket(zmq.PULL)
        url = 'tcp://127.0.0.1:5555'
        s.bind(url)
        while self.running:
            try:
                msg = s.recv(zmq.NOBLOCK)  # note NOBLOCK here
            except zmq.Again:
                # no message to recv, do other things
                time.sleep(0.01)
            else:
                if msg == 'ENABLE' and not self.active:  # trigger only if not already active
                    self.active = True

    def cleanup(self):
        print('Cleaning up and exiting gracefully.')
        self.running = False  # deactivate all loops
        self.active = True
        self.switch('ON', self.yubi_id_l)


if __name__ == "__main__":
    print("Started.")
    yl = YubiLock()
