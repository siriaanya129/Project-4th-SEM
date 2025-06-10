import React from 'react';
// useNavigate is no longer needed here
import styles from './ProfilePanel.module.css';

const ProfilePanel = ({ isOpen, onClose, user, onLogout }) => {
  
  const backdropClasses = `${styles.backdrop} ${isOpen ? styles.active : ''}`;
  const panelClasses = `${styles.panel} ${isOpen ? styles.active : ''}`;

  return (
    <div className={backdropClasses} onClick={onClose}>
      <div className={panelClasses} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>My Profile</h3>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.body}>
          <div className={styles.userInfo}>
            <h4>{user?.username || 'Loading...'}</h4>
            <p>{user?.email || 'Loading...'}</p>
          </div>
          <button onClick={onLogout} className={styles.logoutButton}>
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePanel;