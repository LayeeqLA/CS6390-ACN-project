# CS6390 ACN PROJECT Fall 2024
## LAYEEQ AHMED [LXA230013]
## ENV DETAILS

- Built using Python 3.6.5
- Tested on csgrads1 server

## SOURCE FILES
- `node.py` - for running a node for a given topology
- `controller.py` - for processing input and output message for a given topology

## STEPS TO RUN

- First, a `topology` file is required, in which each line represents a unidirectional edge between nodes. For example, "x y" line indicates there is a unidirectional edge from x to y.
- Second, a node can be run in the following configuration:
	- Node is a sender: `./node.py <ID> sender "<message>" <duration> &`
	- Node is a receiver: `./node.py <ID> receiver <SID> <duration> &`
	- Node is neither a sender nor a receiver: `./node.py <ID> <duration> &`  
where `SID` is the ID of the sender whose tree the receiver wants to join, `duration` is the time in seconds for the nodes to execute and `message` is the data that the sends to all its receivers.  
**Do note that message has to be enclosed in "" to avoid issues with spaces and treat to it as a single string message.**
- Third, controller is run using `./controller.py <duration> &`, where `duration` is the time in seconds for the controller to execute.  
  
**NOTE1: A sample scenario file `scenario1` has been provided for reference.**  
**NOTE2: `topology` file has to be present in the folder of execution.**  
**NOTE3: Assumes a system of maximum ten nodes (node IDs 0...9)**  
  
## FILES GENERATED DURING EXECUTION
- `input_x`: incoming messages are received by node `x` through this file
- `output_x`: outgoing messages from node `x` are written to this file
- `R_received_from_S`: this file contains the messages received from sender `S` by receiver `R` after joining its tree
- `node_x.log`: this file that contains debugging logs for node `x` (can be ignored)