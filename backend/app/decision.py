from database import save_settings, get_setting_value
from controller_actions import redirect_traffic_full, block_ip, rate_limit_for_host, redirect_to_intermediate_ovs

# Confidence rates for different data sources
CONFIDENCE_RATES = {
    "Netflow": 0.2,
    "AD-logs": 0.3,
    "Honeypot": 0.8,
    "dns-logs": 0.25,
    "EDR": 0.7,
    "IDS": 0.6
}

# Detection mode thresholds
DETECTION_MODES = {
    "strict": 0.8,
    "balanced": 0.5,
    "loose": 0.2
}

def get_or_initialize_marks(sourceip):
    """
    Retrieve marks from the database or initialize them if not present.

    Args:
        sourceip (str): The source IP address.

    Returns:
        float: The marks associated with the source IP, initialized to 0.0 if not found.
    """
    key = f"{sourceip} marks"
    marks = get_setting_value(key)
    if marks:
        # If marks exist, return as a float
        return float(marks)
    else:
        # If marks don't exist, initialize with 0.0
        save_settings({key: "0.0"})
        return 0.0




def save_marks(sourceip, marks):
    """
    Save marks to the database.

    Args:
        sourceip (str): The source IP address.
        marks (float): The marks to save.
    """
    save_settings({f"{sourceip} marks": str(marks)})


def process_event(event):
    """
    Process an incoming event, calculate marks, update them, and take appropriate actions.

    Args:
        event (dict): The event containing 'Source', 'Score', and 'SourceIP'.

    Returns:
        list: A list of actions taken (for informational purposes).
    """
    source = event.get("Source")
    score = float(event.get("Score", 0))
    source_ip = event.get("SourceIP")

    # Retrieve detection mode and honeypot IP from database
    detection_mode = get_setting_value("Mode")
    honeypot_ip = get_setting_value("Honeypot IP Address")
    if not detection_mode or not honeypot_ip:
        print("Error: Detection mode or honeypot IP not set in database.")
        return []

    if source not in CONFIDENCE_RATES or detection_mode not in DETECTION_MODES:
        print("Invalid source or detection mode.")
        return []

    confidence_rate = CONFIDENCE_RATES[source]
    detection_multiplier = DETECTION_MODES[detection_mode]

    # Calculate marks increase
    marks_increase = score * confidence_rate * detection_multiplier

    # Update marks for SourceIP
    marks = get_or_initialize_marks(source_ip)
    updated_marks = marks + marks_increase
    save_marks(source_ip, updated_marks)

    actions = []  # List to collect actions for informational purposes

    # Take actions based on marks thresholds
    if updated_marks >= 100:
        block_ip(src_ip=f"{source_ip}/32", admin_or_automated="Automated")
        actions.append("Block")
    elif updated_marks >= 60:
        redirect_traffic_full(source_ip, honeypot_ip, admin_or_automated="Automated")
        actions.append("Redirect")
    elif updated_marks >= 40:
        rate_limit_for_host(
            source_ip,
            rate_limit_bps=50,
            admin_or_automated="Automated"  # Mark the action as automated
        )
        actions.append("Rate Limit")
    elif updated_marks >= 20:
        redirect_to_intermediate_ovs(source_ip, ovs_id="of:0000000000000003", admin_or_automated="Automated")
        actions.append("Intermediate Redirect")
    else:
        actions.append("No Action") 

    return actions
