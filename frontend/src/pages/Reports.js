import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Reports.css';

function Reports() {
  const [reportType, setReportType] = useState('anomalies');
  const [reportData, setReportData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch report data from the backend
  useEffect(() => {
    const fetchReportData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/get-report', {
          params: { time_range: 'monthly', report_type: reportType },
        });
        setReportData(response.data.data);
      } catch (err) {
        setError('Failed to fetch report data. Please try again.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReportData();
  }, [reportType]);

  // Handle PDF download
  const handleDownloadPDF = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/download-pdf', {
        params: { time_range: 'monthly', report_type: reportType },
        responseType: 'blob', // Ensure response is treated as a binary file
      });

      // Create a download link dynamically
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `${reportType}_report_monthly.pdf`;
      document.body.appendChild(link); // Append to body
      link.click(); // Simulate click
      document.body.removeChild(link); // Cleanup
    } catch (err) {
      setError('Failed to download the PDF. Please try again.');
      console.error(err);
    }
  };

  return (
    <div className="reports">
      <h2>Generate Monthly Reports</h2>

      <div className="report-filters">
        <label htmlFor="report-type">Report Type:</label>
        <select
          id="report-type"
          value={reportType}
          onChange={(e) => setReportType(e.target.value)}
        >
          <option value="anomalies">Anomalies</option>
          <option value="actions">Actions</option>
        </select>

        <button onClick={handleDownloadPDF}>Download PDF</button>
      </div>

      <div className="report-display">
        <h3>{reportType} Report (Monthly)</h3>
        {isLoading ? (
          <p>Loading...</p>
        ) : error ? (
          <p className="error">{error}</p>
        ) : (
          <table>
            <thead>
              <tr>
                {reportData.length > 0 &&
                  Object.keys(reportData[0]).map((key) => <th key={key}>{key.toUpperCase()}</th>)}
              </tr>
            </thead>
            <tbody>
              {reportData.length > 0 ? (
                reportData.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, idx) => (
                      <td key={idx}>{value || 'N/A'}</td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="100%">No data available</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Reports;
