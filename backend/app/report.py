from flask import jsonify, make_response
import pdfkit  # For generating PDFs
from datetime import datetime, timedelta
from database import get_anomalies, get_actions

class ReportGenerator:
    def filter_data_by_monthly(self, data):
        """
        Filter the provided data for the past 30 days.

        Args:
            data (list): List of dictionaries containing the data to filter.

        Returns:
            list: Filtered data.
        """
        now = datetime.now()
        cutoff = now - timedelta(days=30)

        filtered_data = [
            item for item in data if datetime.fromisoformat(item['timestamp']) > cutoff
        ]

        return filtered_data

    def generate_report(self, report_type):
        """
        Generate a report for the past 30 days.

        Args:
            report_type (str): The type of report ('anomalies', 'actions').

        Returns:
            dict: The report data.
        """
        if report_type == 'anomalies':
            anomalies = get_anomalies()
            data = self.filter_data_by_monthly(anomalies)
        elif report_type == 'actions':
            actions = get_actions()
            data = self.filter_data_by_monthly(actions)
        else:
            raise ValueError("Invalid report type")
        return {"report_type": report_type, "time_range": "monthly", "data": data}

    def generate_pdf_report(self, report_type):
        """
        Generate a PDF report for the past 30 days.

        Args:
            report_type (str): The type of report ('anomalies', 'actions').

        Returns:
            bytes: The PDF content.
        """
        report_data = self.generate_report(report_type)

        if not report_data['data']:
            html_content = f"""
            <html>
            <head><title>{report_type.capitalize()} Report</title></head>
            <body>
                <h1>{report_type.capitalize()} Report</h1>
                <h2>Time Range: Monthly</h2>
                <p>No data available for the selected time range.</p>
            </body>
            </html>
            """
        else:
            html_content = f"""
            <html>
            <head><title>{report_type.capitalize()} Report</title></head>
            <body>
                <h1>{report_type.capitalize()} Report</h1>
                <h2>Time Range: Monthly</h2>
                <table border="1">
                    <thead>
                        <tr>{"".join(f"<th>{key.capitalize()}</th>" for key in report_data['data'][0].keys() if key)}</tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr>{''.join(f'<td>{value if value is not None else "N/A"}</td>' for value in item.values())}</tr>" for item in report_data['data'])}
                    </tbody>
                </table>
            </body>
            </html>
            """
        try:
            pdf_content = pdfkit.from_string(html_content, False)
            return pdf_content
        except Exception as e:
            raise
