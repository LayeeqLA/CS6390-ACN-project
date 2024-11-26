#!/usr/bin/env python3


import sys

LOGFILE_STR = "../log/node-{}.log"
INIT_ERROR_STR = (
    "Incorrect argument length. Expected: `./node.py node-id [mode] [string] duration`."
)
SENDER = "sender"
RECEIVER = "receiver"


class Node:

    def __init__(self):

        self.id = None
        self.mode = None
        self.duration = None
        self.string = None
        self.senderId = None
        self.logfile = None

        match (len(sys.argv)):
            case 3:
                # neither sender/receiver -> only duration
                try:
                    self.id = int(sys.argv[1])
                    self.duration = int(sys.argv[2])
                    self.logfile = open(LOGFILE_STR.format(self.id), "wt")
                except:
                    print(INIT_ERROR_STR)
                    exit(1)

            case 5:
                # node is a sender or receiver
                try:
                    self.id = int(sys.argv[1])
                    self.duration = int(sys.argv[4])
                    self.logfile = open(LOGFILE_STR.format(self.id), "wt")
                except:
                    print(INIT_ERROR_STR)
                    exit(1)

                self.mode = sys.argv[2]
                if self.mode == SENDER:
                    self.string = sys.argv[3]
                elif self.mode == RECEIVER:
                    try:
                        self.senderId = int(sys.argv[3])
                    except:
                        self.write_log(f"Invalid senderId: {sys.argv[3]}")
                        exit(1)
                else:
                    self.write_log(f"Invalid node mode: {sys.argv[2]}")
                    exit(1)

            case _:
                print(INIT_ERROR_STR)
                exit(1)

        # log the config
        self.write_log(f"*****STARTED NODE SERVICE*****")
        self.write_log(f"ID: {self.id}")
        self.write_log(f"Mode: {self.mode}")
        if self.mode == SENDER:
            self.write_log(f"Send String: '{self.string}'")
        if self.mode == RECEIVER:
            self.write_log(f"Sender ID: {self.senderId}")
        self.write_log(f"Duration: {self.duration}")

    def write_log(self, value=""):
        if type(value) != str:
            value = str(value)
        self.logfile.write(value + "\n")

    def execute(self):
        for time in range(self.duration):
            self.write_log(time)

    def __del__(self):
        if self.logfile:
            self.write_log("****END****")
            self.logfile.close()


if __name__ == "__main__":
    Node().execute()
