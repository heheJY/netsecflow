from elasticsearch import Elasticsearch

def get_documents_by_ip(elk_host, username, password, ip_address):
    """
    Retrieve documents from all relevant indices in Elasticsearch that match a specific IP address.

    Args:
        elk_host (str): The Elasticsearch host URL (e.g., "http://192.168.102.1:9200").
        username (str): The Elasticsearch username.
        password (str): The Elasticsearch password.
        ip_address (str): The IP address to match.

    Returns:
        dict: A dictionary with index names as keys and lists of matching documents as values.
    """
    es = Elasticsearch(
        elk_host,
        basic_auth=(username, password),
    )

    if not es.ping():
        raise ConnectionError(f"Unable to connect to Elasticsearch at {elk_host}")

    # Indices and their field names
    indices_and_fields = {
        "ad-logs*": "host.ip.keyword",
        "dns-logs*": "host.ip.keyword",
        "elastiflow*": "client.ip.keyword",
        "cowrie-logs*": "host.ip.keyword"
    }

    results = {}

    for index, field in indices_and_fields.items():
        query = {
            "query": {
                "match": {
                    field: ip_address
                }
            },
            "sort": [
                {"@timestamp": {"order": "desc"}}
            ]
        }

        try:
            response = es.search(index=index, body=query, size=50)
            documents = [hit["_source"] for hit in response["hits"]["hits"]]
            results[index] = documents
        except Exception as e:
            # Log or handle the error for each index
            results[index] = f"Error querying index: {str(e)}"
    return results
