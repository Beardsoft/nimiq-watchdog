# Nimiq Watchdog

[![Docker Image CI](https://github.com/maestroi/nimiq-watchdog/actions/workflows/docker-image.yml/badge.svg)](https://github.com/maestroi/nimiq-watchdog/actions/workflows/docker-image.yml)

Nimiq Watchdog is a Python application designed to monitor the status of a Nimiq node. If the node fails to establish consensus after a certain number of attempts, the application will automatically restart the node.

## Requirements

- Docker
- Python 3.6 or higher
- Docker SDK for Python

## Installation development

1. Clone the repository:

```bash
git clone https://github.com/maestroi/nimiq-watchdog.git
cd nimiq-watchdog
```
2. Install the required Python packages:
    
```bash
pip install -r requirements.txt
```

3. Run the application using the following command:
```bash
python main.py
```

## Setup Docker-compose

1. Clone the repository:

```bash
git clone https://github.com/maestroi/nimiq-watchdog.git
```

2. Create a .env file in the root directory of the project and set the following environment variables:

```bash
NIMIQ_HOST=your_nimiq_host # IP or hostname of your Nimiq node (docker)
NIMIQ_PORT=your_nimiq_port # Port of your Nimiq node (docker)
DOCKER_CONTAINER_NAME=your_container_name # container to restart
RETRY_LIMIT=10 # number of attempts to establish consensus
RETRY_DELAY=10 # delay between attempts
RESTART_DELAY=300 # delay between stopping and starting the container
PROMETHEUS_PORT=12345 # port for Prometheus metrics
```

3. Start the application using the following command:

```bash
docker-compose up -d
```

## Configuration Docker

The application can be configured using environment variables. The following variables are available:
```bash
docker build -t nimiq-watchdog .
```

Set the following environment variables:
```bash
export NIMIQ_HOST=your_nimiq_host
export NIMIQ_PORT=your_nimiq_port
export DOCKER_CONTAINER_NAME=your_container_name
export RETRY_LIMIT=10
export RETRY_DELAY=10
export PROMETHEUS_PORT=12345
```

Start the application using the following command:
```bash
docker run -d --name nimiq-watchdog -v /var/run/docker.sock:/var/run/docker.sock nimiq-watchdog
```

The application will now monitor your Nimiq node and restart it if it fails to establish consensus.

License
This project is licensed under the MIT License - see the LICENSE file for details.
