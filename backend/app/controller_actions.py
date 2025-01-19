import requests
from requests.auth import HTTPBasicAuth
import time
import json
import os
from database import get_setting_value, record_action
from topology import get_topology_data
from generator import point_to_point_intent
# ONOS Controller Credentials
ONOS_CONTROLLER_IP = get_setting_value("SDN Controller IP")
ONOS_API_BASE = f'http://{ONOS_CONTROLLER_IP}:8181/onos/v1'
ONOS_USERNAME = ''
ONOS_PASSWORD = ''
CONFIG_DIRECTORY = 'C:\\netsecflow\\backend\\app\\'

# ONOS Authentication
auth = HTTPBasicAuth(ONOS_USERNAME, ONOS_PASSWORD)

def log_action(action_type, reason, source_ip, admin_or_automated="Admin"):
    """
    Utility function to log actions in the database.
    """
    record_action(action_type=action_type, reason=reason, source_ip=source_ip, admin_or_automated=admin_or_automated)

# Helper: Validate IP address with CIDR format
def is_valid_ip(ip):
    try:
        # Split the IP address into the base address and subnet mask
        base_ip, subnet = ip.split('/')
        # Validate the base IP address
        parts = base_ip.split('.')
        if len(parts) != 4 or not all(0 <= int(part) <= 255 for part in parts):
            return False
        # Validate the subnet mask
        subnet = int(subnet)
        return 0 <= subnet <= 32
    except (ValueError, IndexError):
        return False

def create_acl_rule(
    src_ip=None, dst_ip=None, src_mac=None, dst_mac=None,
    vlan_id=None, eth_type="0x0800", ip_proto="TCP", src_port=None,
    dst_port=None, action="ALLOW"
):
    # Input Validation
    if src_ip and not is_valid_ip(src_ip):
        print(f"Invalid source IP address: {src_ip}")
        return
    if dst_ip and not is_valid_ip(dst_ip):
        print(f"Invalid destination IP address: {dst_ip}")
        return
    if action not in ["ALLOW", "DENY"]:
        print(f"Invalid action: {action}")
        return

    acl_rule = {
        "action": action  # Action can be "ALLOW" or "DENY"
    }
    print(f"Creating ACL rule with ipProto: {ip_proto}")
    if src_ip:
        acl_rule["srcIp"] = src_ip
    if dst_ip:
        acl_rule["dstIp"] = dst_ip
    if src_mac:
        acl_rule["srcMac"] = src_mac
    if dst_mac:
        acl_rule["dstMac"] = dst_mac
    if vlan_id:
        acl_rule["vlanId"] = vlan_id
    if eth_type:
        acl_rule["ethType"] = eth_type
    if ip_proto:
        acl_rule["ipProto"] = ip_proto
    if src_port:
        acl_rule["srcTpPort"] = src_port
    if dst_port:
        acl_rule["dstTpPort"] = dst_port

    url = f"{ONOS_API_BASE}/acl/rules/"
    print(acl_rule)
    try:
        response = requests.post(url, json=acl_rule, auth=auth)
        if response.status_code == 201:
            print(f"Successfully created ACL rule: {acl_rule}")
        else:
            print(f"Failed to create ACL rule: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error creating ACL rule: {e}")


def block_ip(src_ip=None, dst_ip=None, src_mac=None, dst_mac=None, vlan_id=None, eth_type=None, ip_proto=None, src_port=None, dst_port=None, admin_or_automated="Admin"):
    log_action(
        action_type="Block",
        reason=f"Blocked traffic for {src_ip} to {dst_ip}.",
        source_ip=src_ip,
        admin_or_automated=admin_or_automated
    )
    create_acl_rule(
        src_ip=src_ip, dst_ip=dst_ip, src_mac=src_mac, dst_mac=dst_mac,
        vlan_id=vlan_id, eth_type=eth_type, src_port=src_port, dst_port=dst_port, ip_proto=ip_proto,
        action="DENY"
    )    


def allow_ip(src_ip=None, dst_ip=None, src_mac=None, dst_mac=None, vlan_id=None, eth_type=None, ip_proto=None, src_port=None, dst_port=None, admin_or_automated="Admin"):
    log_action(
        action_type="Allow",
        reason=f"Allow traffic from {src_ip} to {dst_ip}.",
        source_ip=src_ip,
        admin_or_automated=admin_or_automated
    )
    create_acl_rule(
        src_ip=src_ip, dst_ip=dst_ip, src_mac=src_mac, dst_mac=dst_mac,
        vlan_id=vlan_id, eth_type=eth_type, src_port=src_port, dst_port=dst_port, ip_proto=ip_proto,
        action="ALLOW"
    )


def redirect_traffic(src_ip, dest_ip, ingress_port, egress_port, device_id, config_name="redirect_intent", admin_or_automated="Admin"):
    if not is_valid_ip(src_ip) or not is_valid_ip(dest_ip):
        print(f"Invalid source or destination IP address: {src_ip}, {dest_ip}")
        return

    # Remove CIDR suffix from dest_ip for ONOS compatibility
    dest_ip_without_cidr = dest_ip.split('/')[0]

    if not ingress_port or not egress_port:
        print("Ingress and egress ports must be specified.")
        return
    
    log_action(
        action_type="Redirect",
        reason=f"Redirected traffic from {src_ip} to {dest_ip}.",
        source_ip=src_ip,
        admin_or_automated=admin_or_automated
    )

    intent = {
        "type": "PointToPointIntent",
        "priority": 40000,
        "appId": "org.onosproject.cli",
        "selector": {
            "criteria": [
                {"type": "ETH_TYPE", "ethType": "0x0800"},  # IPv4 Traffic
                {"type": "IPV4_SRC", "ip": src_ip}   # Match specific source IP
            ]
        },
        "treatment": {
            "instructions": [
                {"type": "L3MODIFICATION", "subtype": "IPV4_DST", "ip": dest_ip_without_cidr}  # Modify destination IP
            ]
        },
        "ingressPoint": {
            "port": ingress_port,
            "device": device_id
        },
        "egressPoint": {
            "port": egress_port,
            "device": device_id
        }
    }

    os.makedirs(CONFIG_DIRECTORY, exist_ok=True)
    file_path = os.path.join(CONFIG_DIRECTORY, f"{config_name}.json")
    with open(file_path, 'w') as json_file:
        json.dump(intent, json_file, indent=4)

    print(f"Intent configuration saved to: {file_path}")

    headers = {'Content-Type': 'application/json'}
    try:
        with open(file_path, 'rb') as json_file:
            response = requests.post(f"{ONOS_API_BASE}/intents", headers=headers, data=json_file.read(), auth=auth)
        if response.status_code == 201:
            print(f"Successfully redirected traffic from {src_ip} to {dest_ip_without_cidr} on device {device_id}")
        else:
            print(f"Failed to redirect traffic: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error redirecting traffic: {e}")

def list_acl_rules():
    try:
        url = f"{ONOS_API_BASE}/acl/rules"
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            return response.json().get('aclRules', [])
        else:
            print(f"Failed to fetch ACL rules: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ACL rules: {e}")
        return []


def unblock_ip(src_ip=None, dst_ip=None, src_port=None, dst_port=None, prefix_length='32',admin_or_automated="Admin"):
    acl_rules = list_acl_rules()
    log_action(
        action_type="Unblock",
        reason=f"Unblock traffic from {src_ip} to {dst_ip}.",
        source_ip=src_ip,
        admin_or_automated=admin_or_automated
    )
    if src_ip and not is_valid_ip(src_ip):
        print(f"Invalid source IP address: {src_ip}")
        return
    if dst_ip and not is_valid_ip(dst_ip):
        print(f"Invalid destination IP address: {dst_ip}")
        return

    if src_ip and '/' not in src_ip:
        src_ip = f"{src_ip}/{prefix_length}"
    if dst_ip and '/' not in dst_ip:
        dst_ip = f"{dst_ip}/{prefix_length}"

    for rule in acl_rules:
        if isinstance(rule, dict):
            rule_src_ip = rule.get("srcIp", "").strip()
            rule_dst_ip = rule.get("dstIp", "").strip()

            if ((src_ip and rule_src_ip == src_ip) or (dst_ip and rule_dst_ip == dst_ip)):
                rule_id = rule.get("id")
                delete_url = f"{ONOS_API_BASE}/acl/rules/{rule_id}"
                try:
                    response = requests.delete(delete_url, auth=auth)
                    if response.status_code == 204:
                        print(f"Successfully unblocked traffic for IP: {src_ip or dst_ip}")
                    else:
                        print(f"Failed to delete ACL rule for IP {src_ip or dst_ip}: {response.text}")
                except requests.exceptions.RequestException as e:
                    print(f"Error deleting ACL rule: {e}")
    print(f"No ACL rule found for IP {src_ip or dst_ip}")

def rate_limit_for_host(host_ip, rate_limit_bps, admin_or_automated="Admin"):
    try:
        # Fetch topology data
        print("Fetching topology data...")
        topology_data = get_topology_data()
        hosts = topology_data.get('hosts', [])

        # Find the host in the topology by its IP address
        print(f"Searching for host with IP {host_ip}...")
        target_host = next((host for host in hosts if host_ip in host.get('ipAddresses', [])), None)
        
        if not target_host:
            print(f"Host with IP {host_ip} not found in the topology.")
            return

        # Resolve the MAC address of the host
        host_mac = target_host.get('mac')
        if not host_mac:
            print(f"MAC address not found for host with IP {host_ip}.")
            return

        # Extract the closest inbound port from the host's location
        locations = target_host.get('locations', [])
        if not locations:
            print(f"No locations found for host {host_ip}.")
            return

        # Use the first location as the closest inbound port
        closest_location = locations[0]
        device_id = closest_location.get('elementId')
        inbound_port = closest_location.get('port')

        if not device_id or not inbound_port:
            print(f"Incomplete location data for host {host_ip}.")
            return

        # Log the action
        log_action(
            action_type="Rate Limit",
            reason=f"Rate limited {host_ip} ({host_mac}) to {rate_limit_bps} bps.",
            source_ip=host_ip,
            admin_or_automated=admin_or_automated
        )

        # Create a meter for rate limiting
        meter_id = str(int(time.time()))  # Generate a unique meter ID
        meter_config = {
            "deviceId": device_id,
            "meterId": meter_id,
            "unit": "KB_PER_SEC",  # Unit for the rate limit
            "bands": [
                {
                    "type": "DROP",
                    "rate": rate_limit_bps,
                    "burstSize": 1000  # Optional burst size
                }
            ]
        }

        # Create the meter on the switch
        print("Creating meter on the device...")
        meter_url = f"{ONOS_API_BASE}/meters/{device_id}"
        meter_response = requests.post(meter_url, json=meter_config, auth=auth)
        if meter_response.status_code != 201:
            print(f"Failed to create meter: {meter_response.text}")
            return

        # Debugging: Fetch all meters to confirm creation
        print("Fetching all meters after creation...")
        meters_response = requests.get(meter_url, auth=auth)
        if meters_response.status_code == 200:
            meters = meters_response.json().get("meters", [])
            print("Meters fetched:", meters)

            # Find the most recent meter for debugging
            latest_meter = next((m for m in meters if m["bands"][0]["rate"] == rate_limit_bps), None)
            if not latest_meter:
                print("Could not find the newly created meter.")
                return
            meter_id = latest_meter["id"]

            # Create a flow with MAC-based selector
            print("Attaching meter to flow...")
            flow_rule = {
                "priority": 41000,
                "timeout": 0,
                "isPermanent": True,
                "deviceId": device_id,
                "treatment": {
                    "instructions": [
                        {"type": "METER", "meterId": meter_id},
                        {"type": "OUTPUT", "port": inbound_port}
                    ]
                },
                "selector": {
                    "criteria": [
                        {"type": "ETH_TYPE", "ethType": "0x0800"},  # IPv4 Traffic
                        {"type": "ETH_DST", "mac": host_mac},  # Match Source MAC
                    ]
                }
            }

            flow_url = f"{ONOS_API_BASE}/flows/{device_id}"
            flow_response = requests.post(flow_url, json=flow_rule, auth=auth)
            if flow_response.status_code == 201:
                print(f"Successfully applied rate limit for {host_ip} ({host_mac}) on port {inbound_port}.")
            else:
                print(f"Failed to apply flow for rate limiting: {flow_response.text}")
        else:
            print(f"Failed to fetch meters: {meters_response.text}")
            return

    except Exception as e:
        print(f"Error applying rate limit for host {host_ip}: {e}")

def calculate_shortest_path(src_device_id, dst_device_id, links):
    """
    Calculate the shortest path between two devices using Dijkstra's algorithm.
    """
    from heapq import heappop, heappush
    import collections

    # Build a graph representation of the topology
    graph = collections.defaultdict(list)
    for link in links:
        src = link['src']
        dst = link['dst']
        latency = float(link['annotations'].get('latency', 1))  # Use latency as weight
        graph[src['device']].append((latency, dst['device'], src['port'], dst['port']))
        graph[dst['device']].append((latency, src['device'], dst['port'], src['port']))

    # Dijkstra's algorithm for shortest path
    queue = [(0, src_device_id, [])]  # (cumulative_latency, current_device, path)
    visited = set()
    while queue:
        latency, device, path = heappop(queue)
        if device in visited:
            continue
        visited.add(device)
        path = path + [device]

        if device == dst_device_id:
            return path

        for next_latency, next_device, _, _ in graph[device]:
            if next_device not in visited:
                heappush(queue, (latency + next_latency, next_device, path))
    return []




def create_point_to_point_intents(source_ip, destination_ip, src_device, dst_device, src_port, dst_port, app_id="org.onosproject.cli", priority=200):
    """
    Create a Point-to-Point Intent to reroute traffic between two devices.
    """
    try:
        intent = {
            "type": "PointToPointIntent",
            "appId": app_id,
            "priority": priority,
            "selector": {
                "criteria": [
                    {"type": "ETH_TYPE", "ethType": "0x0800"},
                    {"type": "IPV4_SRC", "ip": f"{source_ip}/32"}
                ]
            },
            "ingressPoint": {
                "port": str(src_port),
                "device": src_device
            },
            "egressPoint": {
                "port": str(dst_port),
                "device": dst_device
            }
        }

        # Save intent to a JSON file
        filename = f"intent_{src_device.replace(':', '_')}_{dst_device.replace(':', '_')}.json"
        with open(filename, 'w') as file:
            json.dump(intent, file, indent=4)
        print(f"Intent saved to {filename}")

        # Push the intent to ONOS
        url = f"{ONOS_API_BASE}/intents"
        with open(filename, 'r') as file:
            response = requests.post(
                url,
                auth=auth,
                headers={"Content-Type": "application/json"},
                data=file.read()
            )
        if response.status_code == 201:
            print(f"Intent successfully pushed: {filename}")
        else:
            print(f"Failed to push intent: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error creating intent: {e}")

def redirect_traffic_full(source_ip, honeypot_ip, admin_or_automated="Admin"):
    """
    Redirect traffic from a source IP to the honeypot IP through the shortest path.
    """
    log_action(
        action_type="Redirect",
        reason=f"Redirected traffic from {source_ip} to {honeypot_ip}.",
        source_ip=source_ip,
        admin_or_automated=admin_or_automated
    )
    try:
        print("Fetching topology data...")
        topology_data = get_topology_data()
        devices = topology_data.get('devices', [])
        links = topology_data.get('links', [])
        hosts = topology_data.get('hosts', [])

        # Locate source host
        print(f"Finding source host with IP {source_ip}...")
        source_host = next((host for host in hosts if source_ip in host.get('ipAddresses', [])), None)
        if not source_host:
            print(f"Source host with IP {source_ip} not found.")
            return

        # Locate honeypot host
        print(f"Finding honeypot host with IP {honeypot_ip}...")
        honeypot_host = next((host for host in hosts if honeypot_ip in host.get('ipAddresses', [])), None)
        if not honeypot_host:
            print(f"Honeypot host with IP {honeypot_ip} not found.")
            return

        # Extract source and destination device details
        src_location = source_host['locations'][0]
        dst_location = honeypot_host['locations'][0]

        src_device_id = src_location['elementId']
        src_port = src_location['port']
        dst_device_id = dst_location['elementId']
        dst_port = dst_location['port']

        # Determine shortest path
        print(f"Calculating the shortest path from {src_device_id} to {dst_device_id}...")
        path = calculate_shortest_path(src_device_id, dst_device_id, links)
        if not path:
            print("No path found between the source and honeypot.")
            return

        print(f"Shortest path calculated: {path}")

        # Generate the Point-to-Point Intent JSON
        create_point_to_point_intents(
            source_ip=source_ip,
            destination_ip=honeypot_ip,
            src_device=src_device_id,
            dst_device=dst_device_id,
            src_port=src_port,
            dst_port=dst_port
        )

        print("Intent created successfully.")
    except Exception as e:
        print(f"Error redirecting traffic: {e}")

def redirect_to_intermediate_ovs(source_ip, ovs_id, admin_or_automated="Admin"):
    """
    Redirect traffic from a source host to an intermediate Open vSwitch (OVS).
    After reaching the intermediate switch, traffic is forwarded using reactive routing.
    :param source_ip: The IP address of the source host.
    :param ovs_id: The ID of the intermediate Open vSwitch.
    :param admin_or_automated: Indicates if the action is admin-triggered or automated.
    """
    try:
        print("Fetching topology data...")
        topology_data = get_topology_data()
        devices = topology_data.get('devices', [])
        links = topology_data.get('links', [])
        hosts = topology_data.get('hosts', [])

        # Find source host
        print(f"Finding source host with IP {source_ip}...")
        source_host = next((host for host in hosts if source_ip in host.get('ipAddresses', [])), None)
        if not source_host:
            print(f"Source host with IP {source_ip} not found.")
            return

        # Locate the source host's switch and port
        source_location = source_host.get('locations', [])[0]
        src_device_id = source_location.get('elementId')
        ingress_port = source_location.get('port')  # Port nearest to the source host

        # Locate the intermediate switch
        print(f"Finding intermediate Open vSwitch with ID {ovs_id}...")
        intermediate_switch = next((device for device in devices if device['id'] == ovs_id), None)
        if not intermediate_switch:
            print(f"Intermediate Open vSwitch with ID {ovs_id} not found.")
            return

        intermediate_device_id = intermediate_switch['id']

        # Find the link from the source switch to the intermediate switch
        print(f"Finding link from source switch ({src_device_id}) to intermediate switch ({intermediate_device_id})...")
        link_to_intermediate = next(
            (l for l in links if l['src']['device'] == src_device_id and l['dst']['device'] == intermediate_device_id),
            None
        )
        if not link_to_intermediate:
            print(f"No direct link found between {src_device_id} and {intermediate_device_id}.")
            return

        egress_port = link_to_intermediate['src']['port']  # Port on the source switch to the intermediate switch

        print(f"Source switch ingress port: {ingress_port}, egress port: {egress_port}")

        # Log action
        log_action(
            action_type="Redirect",
            reason=f"Redirected traffic from {source_ip} to intermediate switch {ovs_id}.",
            source_ip=source_ip,
            admin_or_automated=admin_or_automated
        )

        # Create the intent to redirect traffic
        intent = {
            "type": "PointToPointIntent",
            "appId": "org.onosproject.cli",
            "priority": 200,
            "selector": {
                "criteria": [
                    {"type": "ETH_TYPE", "ethType": "0x0800"},  # IPv4 Traffic
                    {"type": "IPV4_SRC", "ip": f"{source_ip}/32"}  # Match source IP
                ]
            },
            "ingressPoint": {
                "port": str(ingress_port),
                "device": src_device_id
            },
            "egressPoint": {
                "port": str(egress_port),
                "device": src_device_id  # Same device, but different port
            }
        }

        # Save intent as JSON file
        file_name = f"intent_{src_device_id.replace(':', '_')}_{ovs_id.replace(':', '_')}.json"
        with open(file_name, 'w') as file:
            json.dump(intent, file, indent=4)
        print(f"Intent saved to {file_name}")

        # Submit the intent to ONOS
        headers = {'Content-Type': 'application/json'}
        url = f"{ONOS_API_BASE}/intents"
        with open(file_name, 'r') as file:
            response = requests.post(url, headers=headers, data=file.read(), auth=auth)

        if response.status_code == 201:
            print(f"Successfully redirected traffic from {source_ip} to {ovs_id}.")
        else:
            print(f"Failed to redirect traffic: {response.status_code} {response.text}")

    except Exception as e:
        print(f"Error redirecting traffic: {e}")


def test_rate_limit_for_host():
    """
    Test applying rate limiting on the closest inbound port of a host.
    """
    print("\n--- Testing Rate Limiting for Host ---")
    host_ip = "10.0.0.1" 
    rate_limit_bps = 50

    try:
        rate_limit_for_host(
            host_ip=host_ip,
            rate_limit_bps=rate_limit_bps,
            admin_or_automated="Automated"  # Mark the action as automated
        )
        print(f"Rate limiting test completed for host: {host_ip}")
    except Exception as e:
        print(f"Error during rate limiting test: {e}")


def test_redirect_traffic_full():
    print("\n--- Testing Redirect Traffic Full ---")
    redirect_traffic_full(source_ip="10.0.0.1", honeypot_ip="10.0.0.5", admin_or_automated="Admin")
    print("Redirect test completed successfully.")



