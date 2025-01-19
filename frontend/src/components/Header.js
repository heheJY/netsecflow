// Header.js
import React from 'react';
import './Header.css';
function Header() {
  return (
    <div className="header">
      <h1>NetSecFlow</h1>
      <div className="user-info">
        <span>Admin</span>
        <button>Logout</button>
      </div>
    </div>
  );
}

export default Header;
