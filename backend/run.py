from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sys

# Insert path for controller actions
sys.path.insert(1, 'app/')
from controller_actions import block_ip, allow_ip, rate_limit_for_host, redirect_traffic_full, unblock_ip
from topology import get_topology_data
from reception import webhook
from database import save_settings, get_settings, get_flows, get_actions, get_setting_value, get_anomalies, delete_event_entry
from app_logging import log_flows_to_database
from service_stat import get_service_status
from query_elastic import get_documents_by_ip
from chatbot import handle_chatbot_request
from report import ReportGenerator
import os
# Initialize the Flask app
app = Flask(__name__)
report_generator = ReportGenerator()
PDF_DIRECTORY = os.path.abspath("generated_reports")

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

app.add_url_rule('/webhook', view_func=webhook, methods=['POST'])

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No question provided"}), 400
    response = handle_chatbot_request(user_question)
    return jsonify({"answer": response})

@app.route('/api/get-report', methods=['GET'])
def get_report():
    try:
        report_type = request.args.get('report_type')
        report_data = report_generator.generate_report(report_type)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-pdf', methods=['GET'])
def download_pdf():
    try:
        report_type = request.args.get('report_type', 'anomalies')
        
        filepath = os.path.join(PDF_DIRECTORY, f"{report_type}_report_monthly.pdf")
        if not os.path.exists(filepath):
            pdf_content = report_generator.generate_pdf_report(report_type)
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
        return send_file(filepath, as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/get-documents-by-ip', methods=['POST'])
def get_documents():
    """
    Retrieve documents across all indices for a given IP address.
    """
    data = request.json
    ip_address = data.get("ip_address")

    if not ip_address:
        return jsonify({"error": "IP address is required"}), 400

    elk_host = "http://192.168.102.1:9200"
    username = "elastic"
    password = "T5fkob-BmswSUWNJ9uzA"

    try:
        results = get_documents_by_ip(elk_host, username, password, ip_address)
        return jsonify({"data": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/service-status', methods=['GET'])
def fetch_service_status():
    """
    Endpoint to fetch the statuses of SIEM (ELK), Honeypot (Cowrie), and SDN Controller (ONOS).
    """
    try:
        ONOS_CONTROLLER_IP = get_setting_value("SDN Controller IP")
        ELK_IP = get_setting_value("ELK IP Address")
        service_status = get_service_status(ELK_IP,ONOS_CONTROLLER_IP)  # Call the function to get service statuses
        return jsonify({"data": service_status}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ignore', methods=['POST'])
def ignore_event():
    """
    Endpoint to delete an event from the events table based on the source IP.
    """
    data = request.json
    source_ip = data.get('srcIp')

    if not source_ip:
        return jsonify({"error": "Source IP is required"}), 400
    try:
        delete_event_entry(source_ip)
        return jsonify({"message": f"Event for Source IP {source_ip} ignored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/get-actions', methods=['GET'])
def fetch_actions():
    """
    Endpoint to fetch all actions from the database.
    """
    try:
        actions = get_actions()
        return jsonify({"data": actions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-anomalies', methods=['GET'])
def fetch_anomalies():
    """
    Endpoint to fetch recent anomalies from the events table.
    """
    try:
        anomalies = get_anomalies()
        return jsonify({"data": anomalies}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-flows', methods=['POST'])
def save_flow_data():
    """
    Endpoint to save flow data to the database by fetching from the ONOS controller.
    """
    try:
        log_flows_to_database()
        return jsonify({"message": "Flows fetched and saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-flows', methods=['GET'])
def fetch_flow_data():
    """
    Endpoint to fetch all flow data from the database.
    """
    try:
        flows = get_flows()
        return jsonify({"data": flows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-settings', methods=['POST'])
def save_system_settings():
    """
    Endpoint to save system settings.
    """
    try:
        settings = request.json
        save_settings(settings)
        return jsonify({"message": "Settings saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-settings', methods=['GET'])
def fetch_system_settings():
    """
    Endpoint to fetch all system settings.
    """
    try:
        settings = get_settings()
        return jsonify({"data": settings}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/block', methods=['POST'])
def block():
    """
    Endpoint to block traffic using an ACL with multiple criteria.
    """
    data = request.json
    
    # Extract ACL parameters from request
    src_ip = data.get('srcIp', None)
    dst_ip = data.get('dstIp', None)
    src_mac = data.get('srcMac', None)
    dst_mac = data.get('dstMac', None)
    vlan_id = data.get('vlanId', None)
    eth_type = data.get('ethType', None)
    src_port = data.get('srcPort', None)
    dst_port = data.get('dstPort', None)
    prefix_length = data.get('prefixLength', '32')  # Default to /32 if not provided
    duration = data.get('duration', None)
    ip_proto = data.get("ipProto")  

    # Ensure the source and destination IP addresses are in the correct format (add prefix if missing)
    if src_ip and '/' not in src_ip:
        src_ip = f"{src_ip}/{prefix_length}"
    if dst_ip and '/' not in dst_ip:
        dst_ip = f"{dst_ip}/{prefix_length}"

    # Call block_ip function with all the extracted parameters
    block_ip(src_ip=src_ip, dst_ip=dst_ip, src_mac=src_mac, dst_mac=dst_mac,
             vlan_id=vlan_id, eth_type=eth_type,ip_proto=ip_proto, src_port=src_port, dst_port=dst_port)

    return jsonify({"message": f"Blocked traffic for {src_ip} successfully"}), 200

@app.route('/api/topology', methods=['GET'])
def get_topology():
    """
    Endpoint to fetch the network topology from ONOS controller.
    """
    try:
        # Fetch the topology data by calling the function in topology.py
        topology_data = get_topology_data()
        return jsonify(topology_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/allow', methods=['POST'])
def allow():
    """
    Endpoint to allow traffic using an ACL with multiple criteria.
    """
    data = request.json

    # Extract ACL parameters from request
    src_ip = data.get('srcIp', None)
    dst_ip = data.get('dstIp', None)
    src_mac = data.get('srcMac', None)
    dst_mac = data.get('dstMac', None)
    vlan_id = data.get('vlanId', None)
    eth_type = data.get('ethType', None)
    src_port = data.get('srcPort', None)
    dst_port = data.get('dstPort', None)
    prefix_length = data.get('prefixLength', '32')  # Default to /32 if not provided
    duration = data.get('duration', None)

    # Ensure the IP addresses are in the correct format
    if '/' not in src_ip:
        src_ip = f"{src_ip}/{prefix_length}"
    if dst_ip and '/' not in dst_ip:
        dst_ip = f"{dst_ip}/{prefix_length}"

    # Call allow_ip function with all the extracted parameters
    try:
        allow_ip(src_ip=src_ip, dst_ip=dst_ip, src_mac=src_mac, dst_mac=dst_mac,
             vlan_id=vlan_id, eth_type=eth_type, src_port=src_port, dst_port=dst_port)
        return jsonify({"message": f"Allowed traffic for {src_ip} to {dst_ip} successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/rate-limit', methods=['POST'])
def apply_rate_limit():
    """
    Endpoint to apply rate limiting to traffic for a specific host by its IP address.
    """
    data = request.json
    host_ip = data.get('hostIp')  # IP address of the host
    rate_limit_bps = data.get('rateLimitBps')  # Rate limit in bits per second
    admin_or_automated = data.get('adminOrAutomated', 'Admin')  # Specify if it's admin or automated

    # Ensure all required parameters are present
    if not all([host_ip, rate_limit_bps]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Apply rate limiting using the updated function
        rate_limit_for_host(host_ip=host_ip, rate_limit_bps=rate_limit_bps, admin_or_automated=admin_or_automated)
        return jsonify({"message": f"Rate limit applied for host {host_ip} at {rate_limit_bps} bps"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/redirect', methods=['POST'])
def redirect():
    """
    Endpoint to redirect traffic from one IP address to another.
    """
    data = request.json
    src_ip_address = data.get('srcIp')
    redirect_ip_address = data.get('redirectIp')

    if not src_ip_address or not redirect_ip_address:
        return jsonify({"error": "Source IP and Redirect IP must be provided"}), 400

    try:
        # Use redirect_traffic_full to perform the redirection
        redirect_traffic_full(source_ip=src_ip_address, honeypot_ip=redirect_ip_address, admin_or_automated="Admin")
        return jsonify({"message": f"Redirected traffic from {src_ip_address} to {redirect_ip_address} successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/redirectHoney', methods=['POST'])
def redirect_to_honeypot():
    """
    Endpoint to redirect traffic from a given source IP to the honeypot.
    """
    data = request.json
    src_ip = data.get('srcIp')

    if not src_ip:
        return jsonify({"error": "Source IP must be provided"}), 400

    # Get honeypot IP from database settings
    honeypot_ip = get_setting_value("Honeypot IP Address")
    if not honeypot_ip:
        return jsonify({"error": "Honeypot IP not configured in settings"}), 500

    try:
        # Use redirect_traffic_full to perform the redirection
        redirect_traffic_full(source_ip=src_ip, honeypot_ip=honeypot_ip, admin_or_automated="Admin")
        return jsonify({"message": f"Redirected traffic from {src_ip} to honeypot ({honeypot_ip}) successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/api/unblock', methods=['POST'])
def unblock():
    """
    Endpoint to unblock traffic by removing the ACL rule for the specified IP address.
    """
    data = request.json
    src_ip = data.get('srcIp', None)
    dst_ip = data.get('dstIp', None)
    prefix_length = data.get('prefixLength', '32')  # Default to /32 if not provided
    src_port = data.get('srcPort', None)
    dst_port = data.get('dstPort', None)

    # Unblock the IP by removing its ACL rule
    result = unblock_ip(src_ip=src_ip, dst_ip=dst_ip, src_port=src_port, dst_port=dst_port, prefix_length=prefix_length)
    return jsonify({"message": result})


if __name__ == "__main__":
    # Start the Flask app, which includes both the main APIs and the webhook
    app.run(debug=True, host="0.0.0.0", port=5000)
