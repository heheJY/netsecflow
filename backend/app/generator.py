import json
import requests
def save_to_file(filename, data):
    """
    Saves JSON data to a file.
    """
    with open(filename, 'w') as f:
        f.write(data)
    print(f"Intent JSON saved to {filename}")


def point_to_point_intent(source_ip, destination_ip, src_device, dst_device, src_port, dst_port, app_id="org.onosproject.cli", priority=200):
    """
    Create a Point-to-Point Intent to reroute traffic between two devices.

    :param source_ip: The source IP address to match in the selector.
    :param destination_ip: The destination IP address to match in the selector.
    :param src_device: The ingress device ID.
    :param dst_device: The egress device ID.
    :param src_port: The ingress port on the ingress device.
    :param dst_port: The egress port on the egress device.
    :param app_id: The application ID for the intent.
    :param priority: The priority of the intent.
    """
    try:
        # Construct the intent JSON
        intent = {
            "type": "PointToPointIntent",
            "appId": app_id,
            "priority": priority,
            "selector": {
                "criteria": [
                    { "type": "ETH_TYPE", "ethType": "0x0800" },
                    { "type": "IPV4_SRC", "ip": f"{source_ip}/32" },
                    { "type": "IPV4_DST", "ip": f"{destination_ip}/32" }
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

        # Save intent to a JSON file for debugging or submission
        filename = f"intent_{src_device}_{dst_device}.json"
        with open(filename, 'w') as file:
            json.dump(intent, file, indent=4)
        print(f"Intent saved to {filename}")

        # Submit the intent using ONOS REST API
        url = "http://192.168.102.2:8181/onos/v1/intents"
        with open(filename, 'r') as file:
            response = requests.post(
                url,
                auth=('', ''),
                headers={"Content-Type": "application/json"},
                data=file.read()
            )
        if response.status_code == 201:
            print(f"Intent successfully pushed: {filename}")
        else:
            print(f"Failed to push intent: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error creating intent: {e}")


def multipoint_to_singlepoint_intent(app_id, priority, ingress_points, egress_device, egress_port, source_ip=None, dest_ip=None, filename='multipoint_to_singlepoint_intent.json'):
    """
    Generates a Multipoint-to-Singlepoint Intent JSON for ONOS and saves it to a file.
    """
    intent = {
        "type": "MultipointToSinglepointIntent",
        "appId": app_id,
        "priority": priority,
        "ingressPoints": [
            {
                "device": point["device"],
                "port": point["port"]
            } for point in ingress_points
        ],
        "egressPoint": {
            "device": egress_device,
            "port": egress_port
        },
    }

    # Add IP selectors if provided
    if source_ip and dest_ip:
        intent["selector"] = {
            "criteria": [
                {
                    "type": "IPV4_SRC",
                    "ip": f"{source_ip}/32"
                },
                {
                    "type": "IPV4_DST",
                    "ip": f"{dest_ip}/32"
                }
            ]
        }

    # Convert to JSON and save to file
    intent_json = json.dumps(intent, indent=4)
    save_to_file(filename, intent_json)
    return intent_json


def broadcast_intent(app_id, priority, ingress_device, ingress_port, broadcast_group, filename='broadcast_intent.json'):
    """
    Generates a Broadcast Intent JSON for ONOS and saves it to a file.
    """
    intent = {
        "type": "BroadcastIntent",
        "appId": app_id,
        "priority": priority,
        "ingressPoint": {
            "device": ingress_device,
            "port": ingress_port
        },
        "broadcastGroup": [
            {
                "device": device["device"],
                "port": device["port"]
            } for device in broadcast_group
        ]
    }

    # Convert to JSON and save to file
    intent_json = json.dumps(intent, indent=4)
    save_to_file(filename, intent_json)
    return intent_json


def vlan_intent(app_id, priority, ingress_device, ingress_port, vlan_id, treatment_vlan_id=None, filename='vlan_intent.json'):
    """
    Generates a VLAN-based Intent JSON for ONOS and saves it to a file.
    """
    intent = {
        "type": "VlanIntent",
        "appId": app_id,
        "priority": priority,
        "ingressPoint": {
            "device": ingress_device,
            "port": ingress_port
        },
        "selector": {
            "criteria": [
                {
                    "type": "VLAN_VID",
                    "vlanId": vlan_id
                }
            ]
        }
    }

    # Add VLAN modification treatment if provided
    if treatment_vlan_id:
        intent["treatment"] = {
            "instructions": [
                {
                    "type": "VLAN_PUSH",
                    "vlanId": treatment_vlan_id
                }
            ]
        }

    # Convert to JSON and save to file
    intent_json = json.dumps(intent, indent=4)
    save_to_file(filename, intent_json)
    return intent_json
