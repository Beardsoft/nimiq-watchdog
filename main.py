import os
import time
import json
import logging
import requests
import docker
from prometheus_client import start_http_server, Gauge, Counter

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s — %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    handlers=[logging.StreamHandler()])

# Nimiq node connection details
NIMIQ_HOST = os.getenv('NIMIQ_HOST', 'node')
NIMIQ_PORT = int(os.getenv('NIMIQ_PORT', 8648))
# Prometheus
PROMETHEUS_PORT = os.getenv('PROMETHEUS_PORT', 12345)
prom_initial_sync = Gauge('nimiq_watchdog_initial_sync', 'consensus status 1=established, 0=not established')
prom_current_health = Gauge('nimiq_watchdog_current_health', 'consensus status 1=established, 0=not established')
prom_current_epoch = Gauge('nimiq_watchdog_current_epoch', 'current epoch number')
prom_current_batch = Gauge('nimiq_watchdog_current_batch', 'current batch number')
prom_container_restarts = Counter('nimiq_watchdog_container_restarts', 'Number of Docker container restarts')

RETRY_LIMIT = int(os.getenv('RETRY_LIMIT', 1))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 2))  # in seconds
RESTART_DELAY = int(os.getenv('RESTART_DELAY', 300))  # in seconds
DOCKER_CONTAINER_NAME = os.getenv('DOCKER_CONTAINER_NAME', 'node')

client = docker.from_env()

def restart_docker_container(container_name):
    """
    This function restarts a Docker container.
    """
    try:
        container = client.containers.get(container_name)
        container.restart()
        prom_container_restarts.inc()
        logging.info(f"Restarted Docker container: {container_name}")
    except docker.errors.NotFound:
        logging.error(f"No such container: {container_name}")
    except docker.errors.APIError as e:
        logging.error(f"Failed to restart Docker container: {container_name}: {e}")

def isConsensusEstablished():
    """
    This function retrieves consensus data data from a Nimiq node using JSON-RPC.
    If the request fails, it returns None.
    """
    url = f"{NIMIQ_HOST}:{NIMIQ_PORT}"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "isConsensusEstablished",
        "params": []
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        if response.status_code == 200:
            resp_data = json.loads(response.text)
            return resp_data.get('result')
        else:
            logging.error(f"Error fetching consensus: HTTP {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Failed to fetch fetching consensus for: {e}")
        return None

def currentEpoch():
    """
    This function retrieves the current epoch number from a Nimiq node using JSON-RPC.
    If the request fails, it returns None.
    """
    url = f"{NIMIQ_HOST}:{NIMIQ_PORT}"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getEpochNumber",
        "params": []
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        if response.status_code == 200:
            resp_data = response.json()
            epoch = resp_data.get('result', {}).get('data')
            if epoch is not None:
                prom_current_epoch.set(epoch)
            return epoch
        else:
            logging.error(f"Error fetching epoch number: HTTP {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Failed to fetch epoch number: {e}")
        return None

def currentBatch():
    """
    This function retrieves the current batch number from a Nimiq node using JSON-RPC.
    If the request fails, it returns None.
    """
    url = f"{NIMIQ_HOST}:{NIMIQ_PORT}"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBatchNumber",
        "params": []
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        if response.status_code == 200:
            resp_data = response.json()
            batch = resp_data.get('result', {}).get('data')
            if batch is not None:
                prom_current_batch.set(batch)
            return batch
        else:
            logging.error(f"Error fetching batch number: HTTP {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Failed to fetch batch number: {e}")
        return None

def main():
    logging.info("Waiting for initial sync...")
    while True:
        try:
            consensus = isConsensusEstablished()
            if consensus is not None and consensus:
                # If consensus is established, break the loop
                logging.info("Initial sync completed.")
                prom_initial_sync.set(1)
                break
            else:
                logging.info("Initial sync not yet completed, waiting...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logging.error(f"Failed to get consensus: {e}")
            time.sleep(RETRY_DELAY)

    logging.info("Starting continuous monitoring...")
    while True:
        for attempt in range(RETRY_LIMIT):
            try:
                consensus = isConsensusEstablished()
                if consensus is not None and consensus:
                    # If consensus is established, break the loop
                    currentEpoch()
                    currentBatch()
                    prom_current_health.set(1)
                    break
                else:
                    logging.error(f"Consensus not established: Attempt {attempt + 1}")
                    prom_current_health.set(0)
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                logging.error(f"Failed to get consensus: {e}")
                time.sleep(RETRY_DELAY)

        # If we've reached this point, all attempts have failed
        if attempt == RETRY_LIMIT - 1:
            logging.error(f"Failed to establish consensus after {RETRY_LIMIT} attempts, restarting Docker container...")
            restart_docker_container(DOCKER_CONTAINER_NAME)
            logging.info("Sleeping for 5 minutes after restart...")
            time.sleep(RESTART_DELAY)  # Sleep for 5 minutes

if __name__ == "__main__":
    logging.info("Starting Nimiq watchdog...")
    logging.info(f"Version: 0.1.0 ")
    start_http_server(int(PROMETHEUS_PORT))
    logging.info(f"Prometheus metrics available at: http://localhost:{PROMETHEUS_PORT}/metrics")
    logging.info(f"Connecting to Nimiq node at: {NIMIQ_HOST}:{NIMIQ_PORT}")
    while True:
        main()
        time.sleep(1) # Don't want to go too fast
