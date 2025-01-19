import requests
import socket

def is_host_alive(ip, port=None):
    """
    Check if a host is reachable. Optionally, check if a specific port is open.

    Args:
        ip (str): IP address of the host.
        port (int, optional): Port number to check. Default is None.

    Returns:
        bool: True if the host (and port) is reachable, False otherwise.
    """
    try:
        # If port is specified, use socket to check connectivity
        if port:
            with socket.create_connection((ip, port), timeout=3):
                return True
        # Otherwise, just perform a basic reachability check
        socket.gethostbyname(ip)
        return True
    except (socket.timeout, socket.error):
        return False


def check_elk_status(ip):
    """
    Check if the ELK (Elasticsearch) service is running.

    Args:
        ip (str): IP address of the ELK instance.

    Returns:
        bool: True if ELK is responding, False otherwise.
    """
    try:
        response = requests.get(f"http://{ip}:9200", timeout=3, auth=("elastic", ""))
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_onos_status(ip):
    """
    Check if the ONOS SDN Controller is running.

    Args:
        ip (str): IP address of the ONOS instance.

    Returns:
        bool: True if ONOS is responding, False otherwise.
    """
    try:
        response = requests.get(f"http://{ip}:8181/onos/v1/devices", timeout=3, auth=("onos", "rocks"))
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_service_status(elk_ip, onos_ip):
    """
    Retrieve the status of ELK, Honeypot, and ONOS based on the provided IPs.

    Args:
        elk_ip (str): IP address of the ELK instance.
        honeypot_ip (str): IP address of the Honeypot instance.
        onos_ip (str): IP address of the ONOS instance.

    Returns:
        dict: A dictionary with the status of each service.
    """
    # Perform checks for each service
    elk_status = check_elk_status(elk_ip)
    onos_status = check_onos_status(onos_ip)

    return {
        "ELK": "UP" if elk_status else "DOWN",
        "ONOS": "UP" if onos_status else "DOWN",
    }


