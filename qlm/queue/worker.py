import requests
import uuid
from openai import OpenAI
from qlm.endpoints.endpoint import Endpoint


INF = float("inf")
class Worker:
    """
    Worker class that represents a single instance of vLLM in the system.
    """

    def __init__(self, address, port, endpoint):
        """
        Initialize a worker instance. Uses openAI API to communicate with the worker.
        :param address: The address of the worker.
        :param port: The port of the worker.
        """
        self.address = f"http://localhost:{port}"
        self.endpoint= endpoint
        self.openai_api_base = f"{self.address}/v1"
        self.openai_api_key = "EMPTY"
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.openai_api_base,
        )
        self.worker_id = uuid.uuid4()

        print(f"Worker {self.worker_id} registered at {self.address}")

    def add_request(self, prompt, model):
        """
        Add a request to the worker.
        :param prompt: The prompt to be added.
        :param model: The model to be used.
        """

        if self.endpoint.model != model:
            self.endpoint.model_swap(model)

        try:
            completion = self.client.completions.create(model=model, prompt=prompt)

            print("Result of query:", completion)
        except Exception as e:
            print(f"Error in adding request: {e}")

    def _read_metrics(self, metric_name):
        """
        Reads all metrics from the worker and checks for a match with the metric name.
        """
        metrics = requests.get(f"{self.address}/metrics")

        for line in metrics.text.splitlines():
            if line.startswith(metric_name):
                return float(line.split()[-1])

    def get_backpressure(self):
        """
        Get the backpressure of the worker i.e. the number of requests currently being served.
        Includes running, queued and swapped requests.
        return: The backpressure of the worker.
        """

        try:
            running_requests = self._read_metrics("vllm:num_requests_running")
            queued_requests = self._read_metrics("vllm:num_requests_waiting")
            swapped_requests = self._read_metrics("vllm:num_requests_swapped")

            backpressure = running_requests + queued_requests + swapped_requests

            return backpressure
        except Exception as e:
            # If the worker is not reachable, return infinite backpressure
            return INF

    def __hash__(self):
        return hash(self.worker_id)
