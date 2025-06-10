import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCircle } from 'lucide-react'; // ✅ Must be installed via `npm install lucide-react`
import styles from './ProfileSidebar.module.css';

const ProfileSidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (!token) return;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUsername(payload.sub || 'User');
    } catch {
      setUsername('User');
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    navigate('/login');
  };

  return (
    <>
      <div className={styles.profileIconWrapper} onClick={() => setIsOpen(!isOpen)}>
        <UserCircle size={28} />
      </div>
      <div className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
        <div className={styles.sidebarContent}>
          <h3>Logged in as</h3>
          <p className={styles.username}>{username}</p>
          <button className={styles.logoutBtn} onClick={handleLogout}>Logout</button>
        </div>
      </div>
    </>
  );
};

export default ProfileSidebar;
