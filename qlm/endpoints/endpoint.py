import subprocess
import os
import signal
import time
from qlm.config import Config

class Endpoint:
    """
    Endpoint class to start and stop vLLM instances.
    """
    def _start_vllm_server(self):
        """
        Start vLLM server with the given model and port.
        """
        project_dir = os.environ['QLMPROJDIR']

        self.process = subprocess.Popen(['bash', f'{project_dir}/qlm/endpoints/start_vllm.sh', \
                '--model', self.model, \
                '--port', str(self.port)],\
                preexec_fn=os.setsid,
                stdout=subprocess.DEVNULL)

        print('Starting server and wait to load model weights')

        time.sleep(self.config.model_swap_time)

        print('Server started at %s:%d with model %s'
              % (self.address, self.port, self.model))


    def _stop_vllm_server(self):
        """
        Stop vLLM server.
        """
        if self.process == None:
            raise Exception('Server is not started')

        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)

        time.sleep(20)

        print('Server stopped.')


    def __init__(self, model, address, port):
        """
        Initialize the endpoint with the given model, address and port.
        """
        self.model = model
        self.address = address
        self.port = port
        self.config = Config()

        self._start_vllm_server()


    def model_swap(self, new_model):
        """
        Swap the model of the endpoint.
        :param new_model: New model to be swapped.
        """
        self._stop_vllm_server()
        self.model = new_model
        self._start_vllm_server()
