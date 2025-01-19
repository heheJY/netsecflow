import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  return (
    <div className="sidebar">
      <h2 className="sidebar-title">NetSecFlow</h2>
      <ul className="sidebar-menu">
        <li>
          <NavLink to="/" className="nav-link" activeClassName="active" end>
            Dashboard
          </NavLink>
        </li>
        <li>
          <NavLink to="/traffic-overview" className="nav-link" activeClassName="active">
            Traffic Overview
          </NavLink>
        </li>
        <li>
          <NavLink to="/anomaly-detection" className="nav-link" activeClassName="active">
            Anomaly Detection & Alerts
          </NavLink>
        </li>
        <li>
          <NavLink to="/decision-logs" className="nav-link" activeClassName="active">
            Decision Logs
          </NavLink>
        </li>
        <li>
          <NavLink to="/manual-traffic-control" className="nav-link" activeClassName="active">
            Manual Traffic Control
          </NavLink>
        </li>
        <li>
          <NavLink to="/reports" className="nav-link" activeClassName="active">
            Reports
          </NavLink>
        </li>
        <li>
          <NavLink to="/system-settings" className="nav-link" activeClassName="active">
            System Settings
          </NavLink>
        </li>
      </ul>
    </div>
  );
}

export default Sidebar;
