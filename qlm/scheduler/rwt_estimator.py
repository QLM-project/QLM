from qlm.queue.group import Group
from qlm.config import Config


class RWTEstimator:

    def __init__(self):
        self.config = Config()

    def get_waiting_time(self, group):

        num_requests = len(group.requests)
        est_workload_tokens = self.config.workload_tokens
        est_token_throughput = self.config.token_throughput[group.model]

        return num_requests * est_workload_tokens / est_token_throughput
