import openai
import sqlite3
import requests
from elasticsearch import Elasticsearch


# OpenAI API Key
openai.api_key = ""

# Database configuration
DB_PATH = "C:\\netsecflow\\database\\netsecflow.db"

# Elasticsearch configuration
ELASTICSEARCH_URL = "http://192.168.102.1:9200"
elk_client = Elasticsearch(
    ELASTICSEARCH_URL,
    basic_auth=("elastic", ""),
)

def query_database(query, params=()):
    """
    Helper function to execute a query on the database.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def get_mininet_topology():
    """
    Fetch Mininet topology details.
    """
    onos_url = "http://192.168.102.2:8181/onos/v1/topology"
    try:
        response = requests.get(onos_url, auth=("onos", ""))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": "Failed to fetch Mininet topology"}

def fetch_elasticsearch_logs(index, query):
    """
    Fetch logs from Elasticsearch.
    """
    try:
        response = elk_client.search(index=index, body=query)
        return response["hits"]["hits"]
    except Exception as e:
        return []

def generate_gpt_response(prompt, context=None):
    """
    Generate a response from GPT-3.5 using the provided prompt and optional context.
    
    Args:
        prompt (str): The user's question or input.
        context (str, optional): Additional context to provide better responses.
    
    Returns:
        str: The GPT-3.5 response.
    """
    try:
        messages = [{"role": "user", "content": prompt}]
        
        # Add context if provided
        if context:
            context_tokens = len(context.split())  # Count tokens in context
            if context_tokens > 1500:  # Adjust the limit as necessary
                context = " ".join(context.split()[:1500])  # Trim to 1500 tokens
            
            messages.insert(0, {"role": "system", "content": context})
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=messages
        )
        return response['choices'][0]['message']['content']
    except openai.error.InvalidRequestError as e:
        if 'context_length_exceeded' in str(e):
            return "too long"
        raise
    except Exception as e:
        return "Sorry, I couldn't process your request at the moment."


def handle_chatbot_request(user_question):
    """
    Main function to handle chatbot requests.
    Combines database, ELK, and Mininet data into a single context and generates a GPT response.

    Args:
        user_question (str): The user's question.

    Returns:
        str: The response generated by GPT.
    """
    if not user_question:
        return "Please ask a question."

    # Fetch database anomalies/actions as context
    anomalies = query_database("SELECT * FROM events ORDER BY timestamp DESC LIMIT 5")
    actions = query_database("SELECT * FROM actions ORDER BY timestamp DESC LIMIT 5")

    # Fetch recent ELK logs as context
    elk_logs = fetch_elasticsearch_logs("ad-logs*", {"query": {"match_all": {}}})

    # Fetch Mininet topology as context
    topology = get_mininet_topology()

    # Create a combined context
    context = f"""
    Recent Anomalies: {anomalies}
    Recent Actions: {actions}
    ELK Logs: {elk_logs}
    Mininet Topology: {topology}
    """

    # Generate GPT response
    return generate_gpt_response(user_question, context)
