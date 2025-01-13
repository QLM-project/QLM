import asyncio
from collections import deque
from qlm.config import Config
from qlm.queue.virtual_queue_engine import VirtualQueueEngine
from qlm.queue.worker import Worker
from qlm.queue.request import Request
from qlm.endpoints.endpoint import Endpoint


class Queue:
    """
    Queue class is responsible for managing the queue of requests and workers.
    It is responsible for pushing requests to the queue and running the queue.
    """

    def __init__(self):
        """
        Initializes the queue with an empty list of workers, a Config object and a VirtualQueueEngine object.
        """
        self.workers = []
        self.config = Config()
        self.vq_engine = VirtualQueueEngine()

    def register_worker(self, address, port, endpoint):
        """
        Registers a worker with the queue.
        :param address: The address of the worker.
        :param port: The port of the worker.
        """
        worker = Worker(address, port, endpoint)
        self.workers.append(worker)
        self.vq_engine.add_worker(worker)

    def push(self, prompt, model, slo, insertion_time):
        """
        Pushes a request to the virtual queue engine.
        :param prompt: The prompt for the request.
        :param model: The model for the request.
        :param slo: The SLO for the request.
        :param insertion_time: The time at which the request was inserted into the queue. Insertion time is only used for SLO calculation and can be updated during request lifetime.
        """

        new_request = Request(
            prompt=prompt, model=model, slo=slo, insertion_time=insertion_time
        )

        self.vq_engine.add_request(new_request)

    async def run_queue(self):
        """
        Runs the queue. The queue runs in an infinite loop and continuously interacts with the virtual queue engine.
        If a request is found, the queue checks for backpressure and if the worker can handle the request.
        If the worker can handle the request, the request is popped from the virtual queue engine and added to the worker.
        """

        while True:
            self.vq_engine.reorder_vqs()
            for worker in self.workers:
                try:
                    backpressure = worker.get_backpressure()
                    has_request = self.vq_engine.has_request(worker)

                    if has_request and backpressure < self.config.max_batch_size:
                        request_to_serve = self.vq_engine.pop_request(worker)
                        await asyncio.to_thread(
                            worker.add_request,
                            request_to_serve.prompt,
                            request_to_serve.model,
                        )

                except asyncio.CancelledError as e:
                    print("handling cancelled error", e)
