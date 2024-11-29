#!/usr/bin/env python3

import sys, time

LOGFILE_STR = "../log/controller.log"
INFILE_STR = "../out/input_{}"
OUTFILE_STR = "../out/output_{}"
TOPOLOGY_FILE_STR = "../topology"
INIT_ERROR_STR = "Incorrect argument length. Expected: `./controller.py duration`. Duration must be an integer."
FILE_WRITE_FAIL_STR = "Failed to write to file: {} -> will retry"


class Controller:
    def __init__(self):
        self.neighbors: dict[int, list[int]] = dict()
        self.edges = set()
        self.nodes: set[int] = set()
        self.read_counts: list[int] = None
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
                self.edges.add(tuple([int(x) for x in line.split()]))
        self.write_log("Edges: " + str(self.edges))

        for x, y in self.edges:
            neighbor_list = self.neighbors.get(x, [])
            neighbor_list.append(y)
            self.neighbors[x] = neighbor_list
            self.nodes.add(x)
            self.nodes.add(y)
        self.read_counts = [0] * len(self.nodes)
        self.write_log("Nodes: " + str(self.nodes))
        self.write_log("Neighbors list: " + str(self.neighbors))

    def write_log(self, value):
        if type(value) != str:
            value = str(value)
        self.logfile.write(value + "\n")

    def write_in(self, nodeId: int, lines: list[str]):
        if len(lines) == 0:
            return

        done = False
        while not done:
            try:
                with open(INFILE_STR.format(nodeId), "at") as f:
                    f.writelines(lines)
                    # TODO: check if it needs extra \n for each line
                    done = True
            except:
                self.write_log(FILE_WRITE_FAIL_STR.format(INFILE_STR.format(nodeId)))

    def process_messages(self):
        for node in self.nodes:
            messages = None
            try:
                with open(OUTFILE_STR.format(node), "rt") as f:
                    messages = f.readlines()
            except:
                self.write_log("Could not read outfile of node " + node)

            if messages and len(messages) > 0:
                for neighbor in self.neighbors.get(node, []):
                    self.write_in(neighbor, messages[self.read_counts[node] :])
                self.read_counts[node] = len(messages)

    def execute(self):
        for currentTime in range(self.duration):
            self.process_messages()
            self.write_log(f"Finished for time={currentTime}")
            time.sleep(1)

    def __del__(self):
        self.write_log("****END****")
        self.logfile.close()


if __name__ == "__main__":
    Controller().execute()
