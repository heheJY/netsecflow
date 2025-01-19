import React, { useState } from 'react';
import axios from 'axios';

function ManualTrafficControl() {
  const [action, setAction] = useState('block'); // Default action
  const [formData, setFormData] = useState({});
  const [rateLimitBps, setRateLimitBps] = useState('');
  const [hostIp, setHostIp] = useState('');
  const [redirectIp, setRedirectIp] = useState('');

  const resetForm = () => {
    setFormData({});
    setRateLimitBps('');
    setHostIp('');
    setRedirectIp('');
  };

  const handleInputChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const baseUrl = 'http://localhost:5000';
    let endpoint = '';
    let requestBody = {};

    switch (action) {
      case 'block':
      case 'allow':
        endpoint = `/api/${action}`;
        requestBody = { ...formData };
        break;
      case 'rate-limit':
        endpoint = '/api/rate-limit';
        requestBody = { hostIp, rateLimitBps };
        break;
      case 'redirect':
        endpoint = '/api/redirect';
        requestBody = { ...formData, redirectIp };
        break;
      case 'unblock':
        endpoint = '/api/unblock';
        requestBody = { ...formData };
        break;
      default:
        alert('Invalid action selected');
        return;
    }

    try {
      const response = await axios.post(`${baseUrl}${endpoint}`, requestBody);
      alert(response.data.message);
      resetForm();
    } catch (error) {
      console.error('Error:', error.response?.data?.error || error.message);
      alert('Failed to apply action');
    }
  };

  const renderFields = () => {
    switch (action) {
      case 'block':
      case 'allow':
        return (
          <>
            <div className="form-group">
              <label>Source IP:</label>
              <input
                type="text"
                placeholder="Enter Source IP"
                onChange={(e) => handleInputChange('srcIp', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Destination IP:</label>
              <input
                type="text"
                placeholder="Enter Destination IP"
                onChange={(e) => handleInputChange('dstIp', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Source MAC:</label>
              <input
                type="text"
                placeholder="Enter Source MAC"
                onChange={(e) => handleInputChange('srcMac', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Destination MAC:</label>
              <input
                type="text"
                placeholder="Enter Destination MAC"
                onChange={(e) => handleInputChange('dstMac', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>VLAN ID:</label>
              <input
                type="text"
                placeholder="Enter VLAN ID"
                onChange={(e) => handleInputChange('vlanId', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Ethernet Type:</label>
              <input
                type="text"
                placeholder="Enter Ethernet Type (e.g., 0x0800)"
                onChange={(e) => handleInputChange('ethType', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>IP Protocol:</label>
              <select onChange={(e) => handleInputChange('ipProto', e.target.value)}>
                <option value="">None</option>
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
                <option value="ICMP">ICMP</option>
              </select>
            </div>
            <div className="form-group">
              <label>Source Port:</label>
              <input
                type="text"
                placeholder="Enter Source Port"
                onChange={(e) => handleInputChange('srcPort', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Destination Port:</label>
              <input
                type="text"
                placeholder="Enter Destination Port"
                onChange={(e) => handleInputChange('dstPort', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Prefix Length:</label>
              <input
                type="number"
                placeholder="Enter Prefix Length (default 32)"
                onChange={(e) => handleInputChange('prefixLength', e.target.value)}
                min="0"
                max="32"
              />
            </div>
            <div className="form-group">
              <label>Duration (optional):</label>
              <input
                type="number"
                placeholder="Duration in seconds"
                onChange={(e) => handleInputChange('duration', e.target.value)}
              />
            </div>
          </>
        );
      case 'rate-limit':
        return (
          <>
            <div className="form-group">
              <label>Host IP:</label>
              <input
                type="text"
                placeholder="Enter Host IP"
                value={hostIp}
                onChange={(e) => setHostIp(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Rate Limit (Bps):</label>
              <input
                type="number"
                placeholder="Enter Rate Limit"
                value={rateLimitBps}
                onChange={(e) => setRateLimitBps(e.target.value)}
              />
            </div>
          </>
        );
      case 'redirect':
        return (
          <>
            <div className="form-group">
              <label>Source IP:</label>
              <input
                type="text"
                placeholder="Enter Source IP"
                onChange={(e) => handleInputChange('srcIp', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Redirect IP:</label>
              <input
                type="text"
                placeholder="Enter Redirect IP"
                value={redirectIp}
                onChange={(e) => setRedirectIp(e.target.value)}
              />
            </div>
          </>
        );
      case 'unblock':
        return (
          <>
            <div className="form-group">
              <label>Source IP:</label>
              <input
                type="text"
                placeholder="Enter Source IP"
                onChange={(e) => handleInputChange('srcIp', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Destination IP:</label>
              <input
                type="text"
                placeholder="Enter Destination IP"
                onChange={(e) => handleInputChange('dstIp', e.target.value)}
              />
            </div>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div className="manual-traffic-control">
      <h2>Manual Traffic Control</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Action:</label>
          <select value={action} onChange={(e) => setAction(e.target.value)}>
            <option value="block">Block</option>
            <option value="allow">Allow</option>
            <option value="rate-limit">Rate Limit</option>
            <option value="redirect">Redirect</option>
            <option value="unblock">Unblock</option>
          </select>
        </div>

        {renderFields()}

        <button type="submit">Apply Action</button>
        <button type="button" onClick={resetForm} style={{ marginLeft: '10px' }}>
          Reset Form
        </button>
      </form>
    </div>
  );
}

export default ManualTrafficControl;
