# QLM: Queue Management for SLO-oriented LLM Serving [(Paper Link)](https://dl.acm.org/doi/10.1145/3698038.3698523)

QLM is a queue management systen that serves LLM requests with varying SLOs i.e. batch and interactive requests across different models. Optimal ordering of the request queue is critical to maintain these SLOs while ensuring high resource utilization.

----------

## Design 

<img width="500" alt="QLM-design" src="https://github.com/user-attachments/assets/16cd005d-d878-4564-8fd7-f9fc6c984ff6" />

### Formation of Request Groups.
Every incoming request is grouped with other requests that share common perfor-
mance characteristics (such as model and SLO value) to form Request Groups. This converts the complexity of the optimization problem from per-request
level to per-request-group level. By doing so, it alleviates
the scalability challenges and lowers optimization overheads.
Additionally, request groups are a useful abstraction in the
multi-model serving to minimize model swaps and improve request throughput.

### Assigning Request Groups to Virtual Queues. 
Requests in a request group are assigned to a Virtual Queue, representing a waiting queue for an LLM serving instance in the cluster. The ordering of the request groups in a virtual queue determines the execution ordering of the requests on the corresponding LLM serving instance. While requests are assigned to request groups in a first-come-first-serve manner, request groups in a virtual queue are reordered to maximize the SLO attainment for all requests being served.

### RWT Estimator and Scheduler.
At the core of SLO attainment maximization are QLM’s request waiting time (RWT) estimator and global scheduler. Estimates for queue waiting time are used to used by scheduler to reorder the queue. Each request, when being moved to the head of the virtual queue, will be executed on the LLM serving instance. This completes the lifecycle of a request.

## Installation

Any system compatible with vLLM would also work with QLM. If you want to run the LP version of QLM, you will additionally need a Gurobi license.

Run the following command to install the required python packages

```
pip install -r requirements.txt
```

To setup QLM with an editable install, run the following command:

```
pip install -e .
```

----------

## Usage

### Basic Benchmark Test

Setup the project directory variable in shell

```
export QLMPROJDIR=/path/to/qlm
```

Run the following command to test the basic functionality of QLM

```
python benchmarks/basic_test.py
```

### Adding models

In config.yaml file, add the following lines to add a new model

```
token_throughput:
    new_model: xyz
```

Use output token throughput based on vLLM benchmarks.

### Using linear programming (LP) version of QLM 

To use the LP version of QLM, set the Gurobi license variables in the config.yaml file

```
gurobi:
    access_id: "your_access_id"
    secret: "your_secret"
    license: "your_license_id"
```

----------

## Reference


If you find the code useful, please consider citing our work:

```
@inproceedings{qlm,
author = {Patke, Archit and Reddy, Dhemath and Jha, Saurabh and Qiu, Haoran and Pinto, Christian and Narayanaswami, Chandra and Kalbarczyk, Zbigniew and Iyer, Ravishankar},
title = {Queue Management for SLO-Oriented Large Language Model Serving},
year = {2024},
booktitle = {Proceedings of the 2024 ACM Symposium on Cloud Computing},
location = {Redmond, WA, USA},
series = {SoCC '24}
}
```
----------

This project was made possible due to a collaboration between University of Illinois at Urbana-Champaign and IBM Research.

