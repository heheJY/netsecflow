import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import axios from 'axios';
import './TrafficOverview.css';

function TrafficOverview() {
  const networkRef = useRef(null);
  const [topologyData, setTopologyData] = useState({ devices: [], hosts: [], links: [] });
  const [flowData, setFlowData] = useState([]);

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/topology');
        setTopologyData(response.data);
      } catch (error) {
        console.error('Error fetching topology:', error);
      }
    };

    fetchTopology();
  }, []);

  useEffect(() => {
    const fetchFlows = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/get-flows');
        setFlowData(response.data.data);
      } catch (error) {
        console.error('Error fetching flows:', error);
      }
    };

    fetchFlows();
  }, []);

  useEffect(() => {
    const nodes = [];
    const edges = [];
    const processedConnections = new Set();

    topologyData.devices.forEach((device, index) => {
      nodes.push({
        id: device.id,
        label: `Switch ${index + 1}`,
        shape: 'image',
        image: '/icons/switch.png',
      });
    });

    topologyData.hosts.forEach((host, index) => {
      nodes.push({
        id: host.id,
        label: host.ipAddresses[0] || `Host ${index + 1}`,
        shape: 'image',
        image: '/icons/pc.png',
      });

      host.locations.forEach((location) => {
        edges.push({
          from: location.elementId,
          to: host.id,
        });
      });
    });

    topologyData.links.forEach((link) => {
      const connectionId = [link.src.device, link.dst.device].sort().join('-');
      if (!processedConnections.has(connectionId)) {
        processedConnections.add(connectionId);
        edges.push({
          from: link.src.device,
          to: link.dst.device,
          smooth: false,
        });
      }
    });

    const options = {
      nodes: {
        shape: 'dot',
        size: 25,
        font: {
          size: 12,
          color: '#000',
        },
      },
      edges: {
        smooth: false,
        font: {
          size: 0,
        },
        color: { color: '#848484' },
      },
      physics: {
        stabilization: {
          enabled: true,
        },
      },
    };

    if (nodes.length > 0 && edges.length > 0) {
      const container = networkRef.current;
      const networkData = { nodes, edges };
      const network = new Network(container, networkData, options);

      return () => {
        network.destroy();
      };
    }
  }, [topologyData]);

  return (
    <div className="traffic-overview">
      <h2>Traffic Overview</h2>

      <div className="topology-section">
        {/* Network topology visualization */}
        <div className="network-container" ref={networkRef}></div>
      </div>

      <div className="traffic-details">
        {/* Real-time flow table */}
        <h3>Real-Time Flow Table</h3>
        <table>
          <thead>
            <tr>
              <th>Source IP</th>
              <th>Destination IP</th>
              <th>Protocol</th>
              <th>Priority</th>
              <th>App ID</th>
              <th>Device ID</th>
              <th>Bandwidth</th>
              <th>Flow Duration</th>
            </tr>
          </thead>
          <tbody>
            {flowData.map((flow, index) => (
              <tr key={index}>
                <td>{flow.source_ip || 'N/A'}</td>
                <td>{flow.destination_ip || 'N/A'}</td>
                <td>{flow.protocol}</td>
                <td>{flow.priority}</td>
                <td>{flow.app_id}</td>
                <td>{flow.device_id}</td>
                <td>{flow.bandwidth} bytes</td>
                <td>{flow.flow_duration} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TrafficOverview;
