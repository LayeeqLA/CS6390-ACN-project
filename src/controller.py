#!/usr/bin/env python3

import sys

LOGFILE_STR = "../log/controller.log"
TOPOLOGY_FILE_STR = "../topology"
INIT_ERROR_STR = "Incorrect argument length. Expected: `./controller.py duration`. Duration must be an integer."


class Controller:
    def __init__(self):
        self.edges = set()
        self.logfile = open(LOGFILE_STR, "wt")
        self.write_log("*****STARTING CONTROLLER*****")

        if len(sys.argv) != 2:
            self.write_log(INIT_ERROR_STR)
            exit(1)

        try:
            self.duration = int(sys.argv[1])
        except:
            self.write_log(INIT_ERROR_STR)
            exit(1)

        self.write_log(f"Duration: {self.duration}")

        # assumes topology file to be in the expected format of unidirectional edges
        with open(TOPOLOGY_FILE_STR, "rt") as f:
            all_lines = f.readlines()
            for line in all_lines:
                if line.strip() == "":
                    continue
                self.edges.add(tuple(line.split()))

        self.write_log("Edges: " + str(self.edges))

    def write_log(self, value):
        if type(value) != str:
            value = str(value)
        self.logfile.write(value + "\n")

    def execute(self):
        for time in range(self.duration):
            self.write_log(time)

    def __del__(self):
        self.write_log("****END****")
        self.logfile.close()


if __name__ == "__main__":
    Controller().execute()
