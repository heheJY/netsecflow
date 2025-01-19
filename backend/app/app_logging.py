import requests
from database import save_flows, get_setting_value

ONOS_CONTROLLER_IP = get_setting_value("SDN Controller IP")
ONOS_API_URL = f'http://{ONOS_CONTROLLER_IP}:8181/onos/v1/flows'
USERNAME = ""
PASSWORD = ""

def fetch_flows_from_onos():
    """
    Fetch flow information from the ONOS controller's REST API.

    Returns:
        list of dict: A list of flow dictionaries retrieved from ONOS.
    """
    try:
        response = requests.get(ONOS_API_URL, auth=(USERNAME, PASSWORD))
        if response.status_code == 200:
            return response.json().get("flows", [])
        else:
            raise Exception(f"Failed to fetch flows. Status code: {response.status_code}, Message: {response.text}")
    except Exception as e:
        raise Exception(f"Error fetching flows from ONOS: {e}")


def filter_flows(raw_flows):
    """
    Filter and format raw flow data retrieved from ONOS for saving into the database.

    Args:
        raw_flows (list of dict): The raw flow data retrieved from the ONOS controller.

    Returns:
        list of dict: A list of formatted flow dictionaries.
    """
    formatted_flows = []
    for flow in raw_flows:
        try:
            # Extract basic flow properties
            flow_id = flow.get("id", "Unknown")
            app_id = flow.get("appId", "Unknown")
            device_id = flow.get("deviceId", "Unknown")
            priority = flow.get("priority", 0)
            bandwidth = flow.get("bytes", 0)
            flow_duration = flow.get("life", 0)

            # Initialize flow details
            source_ip = "Unknown"
            destination_ip = "Unknown"
            protocol = "Unknown"
            eth_type = "Unknown"
            in_port = "Unknown"
            out_port = "Unknown"

            # Extract details from the selector criteria
            for criterion in flow.get("selector", {}).get("criteria", []):
                if criterion.get("type") == "IPV4_SRC":
                    source_ip = criterion.get("ip", "Unknown")
                elif criterion.get("type") == "IPV4_DST":
                    destination_ip = criterion.get("ip", "Unknown")
                elif criterion.get("type") == "ETH_TYPE":
                    eth_type = criterion.get("ethType", "Unknown")
                    if eth_type == "0x800":
                        protocol = "IPv4"
                    elif eth_type == "0x86DD":
                        protocol = "IPv6"
                    else:
                        protocol = "Ethernet"
                elif criterion.get("type") == "IN_PORT":
                    in_port = f"Port {criterion.get('port', 'Unknown')}"
                elif criterion.get("type") == "OUT_PORT":
                    out_port = f"Port {criterion.get('port', 'Unknown')}"

            # Extract destination IP from treatment if missing
            if destination_ip == "Unknown":
                for instruction in flow.get("treatment", {}).get("instructions", []):
                    if instruction.get("type") == "L3MODIFICATION" and instruction.get("subtype") == "IPV4_DST":
                        destination_ip = instruction.get("ip", "Unknown")

            # Add formatted flow data to the list
            formatted_flows.append({
                "id": flow_id,
                "source_ip": source_ip,
                "destination_ip": destination_ip,
                "protocol": protocol,
                "bandwidth": bandwidth,
                "flow_duration": flow_duration,
                "priority": priority,
                "app_id": app_id,
                "device_id": device_id,
                "eth_type": eth_type,
                "in_port": in_port,
                "out_port": out_port,
            })
        except Exception as e:
            print(f"Error processing flow {flow.get('id', 'Unknown')}: {e}")

    return formatted_flows



def log_flows_to_database():
    """
    Retrieve flow data from ONOS, filter it, and save it to the database.
    """
    try:
        # Step 1: Fetch raw flows from ONOS
        raw_flows = fetch_flows_from_onos()
        
        # Step 2: Filter and format the flows
        formatted_flows = filter_flows(raw_flows)
        
        # Step 3: Save the formatted flows to the database
        save_flows(formatted_flows)
        print(f"Successfully saved {len(formatted_flows)} flows to the database.")
    except Exception as e:
        print(f"Error logging flows to the database: {e}")

