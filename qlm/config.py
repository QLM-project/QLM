from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
from vllm.utils import random_uuid
import argparse
import yaml
import os
from time import perf_counter


class Config:
    """
    Config class is responsible for managing the configuration of the queue.
    """
    def __init__(self):
        """
        Initialize config with all relevant parameters from config.yaml file.
        """
        proj_dir = os.environ["QLMPROJDIR"]
        config_file = os.path.join(proj_dir, "qlm/config.yaml")
        with open(config_file, "r") as f:
            config_vals = yaml.safe_load(f)

        self.max_batch_size = config_vals["max_batch_size"]
        self.workload_tokens = config_vals["workload_tokens"]
        self.token_throughput = config_vals["token_throughput"]
        self.slo_granularity = config_vals["slo_granularity"]
        self.model_swap_time = config_vals["model_swap_time"]

        self.gurobi = config_vals["gurobi"]
