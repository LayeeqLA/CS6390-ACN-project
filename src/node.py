#!/usr/bin/env python3


import sys, time

LOGFILE_STR = "../log/node_{}.log"
INFILE_STR = "../out/input_{}"
OUTFILE_STR = "../out/output_{}"
RCVFILE_STR = "../out/{R}_received_from_{S}"
INIT_ERROR_STR = (
    "Incorrect argument length. Expected: `./node.py node-id [mode] [string] duration`."
)
FILE_WRITE_FAIL_STR = "Failed to write to file: {} -> will retry"
SENDER = "sender"
RECEIVER = "receiver"

INFINITY = -1
EXPIRY_TIME = 30  # no longer neighbor if no hello for more than `30 seconds`
HELLO_MSG = "hello {sender}"
DVECTOR_MSG = "dvector {sender} {origin} {distances} in-neighbors {neighbors}"
IN_DIST_MSG = "in-distance {sender} {distances}"
JOIN_MSG = "join {RID} {SID} {PID} {NID}"
DATA_MSG = "data {sender} {root} {string}"


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

    def write_out(self, value: str):
        done = False
        while not done:
            try:
                with open(OUTFILE_STR.format(self.id), "at") as f:
                    f.write(value + "\n")
                    done = True
            except:
                self.write_log(FILE_WRITE_FAIL_STR.format(OUTFILE_STR.format(self.id)))

    def send_hello(self, currentTime: int):
        # send hello message, if it is time for another one
        if currentTime % 5 == 0:
            self.write_out(HELLO_MSG.format(sender=self.id))

    def send_dvector(self, currentTime: int):
        # send a "dvector" message if it is time to do so
        if currentTime % 5 == 0:
            pass

    def send_in_distance(self, currentTime: int):
        # send an "in-distance" message, if it is time to do so
        if currentTime % 5 == 0:
            pass

    def refresh_parent(self, currentTime: int):
        # send join message to each parent of each tree I am involved in, if time to do so
        pass

    def read_input_file(self, currentTime: int):
        # read the input file and process each new message received
        pass

    def execute(self):
        for currentTime in range(self.duration):
            self.write_log(currentTime)  # TODO: remove
            self.send_hello(currentTime)
            self.send_dvector(currentTime)
            self.send_in_distance(currentTime)
            self.refresh_parent(currentTime)
            self.read_input_file(currentTime)
            time.sleep(1)

    def __del__(self):
        if self.logfile:
            self.write_log("****END****")
            self.logfile.close()


if __name__ == "__main__":
    Node().execute()
