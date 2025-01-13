import uuid


class Request:
    """
    Request class to store the request to LLM
    """

    def __init__(self, prompt, model, slo, insertion_time):
        """
        :param prompt: The prompt to be sent to the model
        :param model: The model to be used for the request
        :param slo: The SLO for the request
        :param insertion_time: The time at which the request was inserted into the queue
        """
        self.request_id = uuid.uuid4()
        self.prompt = prompt
        # Default SLO is 10 seconds
        self.slo = slo
        self.model = model
        self.insertion_time = insertion_time

    def __hash__(self):
        return hash(self.request_id)
