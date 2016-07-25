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
        self.running = True  # keeps while loops running
        self.active = False  # ON/OFF master variable
        self.lock = False  # for preventing disabling YubiKey during write process
        self.timestamp = 0  # activated since ...

        # icons:
        self.on_icon = os.path.abspath("./icons/on_icon.svg")
        self.off_icon = os.path.abspath("./icons/off_icon.svg")

        # starting threads:
        try:
            gi_thread = threading.Thread(target=self.get_ids)
            gi_thread.start()

            # disable as default state
            for t in range(300):
                if self.yubi_id_l:
                    self.disable()
                    break
                else:
                    time.sleep(.01)

            to_thread = threading.Thread(target=self.timeout)
            to_thread.start()

            lis_thread = threading.Thread(target=self.listener)
            lis_thread.start()

            while self.running:
                self.enable()

        except (KeyboardInterrupt, SystemExit):
            self.cleanup()
        finally:
            to_thread.join()
            lis_thread.join()
            sys.exit(0)

    def get_ids(self):
        old_id_l = []
        while self.running:
            # re-enabling old slots in case of change:
            if old_id_l != self.yubi_id_l:
                for old_id in old_id_l:
                    on_cmd = "xinput --enable {}".format(old_id)
                    shell(on_cmd)

            del self.yubi_id_l[:]  # emptying list

            pat = re.compile(r"(?:Yubikey.*?id=)(\d+)", re.IGNORECASE)

            list_cmd = 'xinput list'
            xinput = shell(list_cmd)

            for line in xinput.stdout:
                match = re.search(pat, line)
                if match:
                    yubi_id = match.groups()
                    self.yubi_id_l.extend(yubi_id)

            old_id_l = self.yubi_id_l

            time.sleep(0.5)

    def enable(self):
        if self.active and self.yubi_id_l:
            for yubi_id in self.yubi_id_l:
                on_cmd = "xinput --enable {}".format(yubi_id)
                shell(on_cmd)
            self.active = True
            self.timestamp = time.time()  # setting timeout

            on_msg = "YubiKey(s) enabled."
            print(on_msg)
            notify(self.on_icon)

            # monitor input from YubiKey
            if self.running:
                mon_thread = threading.Thread(target=self.yubikey_monitor)
                mon_thread.start()
                mon_thread.join()

    def disable(self):
        if not self.lock:
            for yubi_id in self.yubi_id_l:
                print 'disabling: ', yubi_id
                off_cmd = "xinput --disable {}".format(yubi_id)
                shell(off_cmd)

            off_msg = "YubiKey(s) disabled."
            print(off_msg)
            notify(self.off_icon)
            self.active = False

    def timeout(self):
        while self.running:
            if time.time() - self.timestamp > 5 and self.active:
                print('Timeout. Now disabling.')
                self.disable()
            time.sleep(.1)

    def yubikey_monitor(self):
        # forming command to run parallel monitoring processes
        mon_cmd = "xinput test {}"
        multi_mon_cmd = ' & '.join([mon_cmd.format(y_id) for y_id in self.yubi_id_l])

        monitor = shell(multi_mon_cmd)

        # Launch the asynchronous readers of the process' stdout and stderr.
        stdout_queue = Queue.Queue()
        stdout_reader = AsynchronousFileReader(monitor.stdout, stdout_queue)
        stdout_reader.start()

        while not stdout_reader.eof and self.active:
            while not stdout_queue.empty():
                stdout_queue.get()  # emptying queue
                self.lock = True
                time.sleep(.01)
            if self.lock:
                print('Yubikey triggered. Now disabling.')
                self.lock = False  # release lock
                self.disable()
                break

        monitor.kill()
        stdout_reader.join()

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

                elif self.active:
                    print('Already active.')

    def cleanup(self):
        print('Cleaning up and exiting gracefully.')
        self.running = False  # deactivate all loops
        self.active = True
        self.enable()


if __name__ == "__main__":
    print("Started.")
    yl = YubiLock()
