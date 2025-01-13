from qlm.queue.queue import Queue
from qlm.endpoints.endpoint import Endpoint
import asyncio
import time
import json

async def basic_test():
    # Test description
    print("Basic test for QLM")


    # Start vLLM endpoint
    endpoint = Endpoint(address="localhost", port=8000, model="meta-llama/Llama-3.1-8B-Instruct")

    time.sleep(10)

    # Create a Queue object
    q = Queue() 

    # Intialize workers
    q.register_worker("localhost", 8000, endpoint)

    # Run the queue
    queue_run_task = asyncio.create_task(q.run_queue())
    
    # Create sample prompts for the queue
    prompts = ["Whats the captial of France?",
               "Name the eight planets in the solar system."]

    # Push interactive prompts to the queue
    for prompt in prompts:
        q.push(prompt=prompt, model="unsloth/Llama-3.2-1B-Instruct", insertion_time = time.time(), slo=10)


    # Push batch prompts from shareGPT dataset
    dataset_path = "../data/ShareGPT_V3_unfiltered_cleaned_split.json"

    with open(dataset_path, encoding='utf-8') as f:
        dataset = json.load(f)


    # Filter out conversations with less than 2 turns
    dataset = [data for data in dataset if len(data["conversations"]) >= 2]

    
    dataset = [(data["conversations"][0]["value"],
                data["conversations"][1]["value"]) for data in dataset]

    # Push prompts to the queue
    for i in range(min(100,len(dataset))):
        q.push(prompt=dataset[i][0], model="unsloth/Llama-3.2-1B-Instruct", insertion_time = time.time(), slo=1000)

    
if __name__ == "__main__":
    asyncio.run(basic_test())
