import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styles from './Navbar.module.css';
import logo from '../assets/logo.png';
import useAuth from '../hooks/useAuth';

const Navbar = () => {
  const { isLoggedIn } = useAuth();
  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const navigate = useNavigate();

  const username = "Siri"; // Placeholder, can be replaced with real user data later

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    window.dispatchEvent(new Event("storage")); // <-- Ensures useAuth updates
    setPanelOpen(false);
    navigate('/');
  };

  return (
    <>
      <nav className={styles.navbar}>
        <div className={styles.navContainer}>
          <Link to="/" className={styles.navLogo}>
            <img src={logo} alt="EduConnect Logo" />
            <span>EduConnect</span>
          </Link>
          <ul className={styles.navMenu}>
            <li className={styles.navItem}><Link to="/">Home</Link></li>
            <li 
              className={styles.navItem} 
              onMouseEnter={() => setFeaturesOpen(true)}
              onMouseLeave={() => setFeaturesOpen(false)}
            >
              <span className={styles.featuresLink}>Features</span>
              {featuresOpen && (
                <div className={styles.featuresDropdown}>
                  <h3 className={styles.dropdownTitle}>Our Services</h3>
                  <div className={styles.serviceCard}>
                      <h4>Personalized Quizzes</h4>
                      <p>Dynamically generated quizzes tailored to individual student needs.</p>
                  </div>
                  <div className={styles.serviceCard}>
                      <h4>Smart Categorization</h4>
                      <p>Using advanced algorithms, we classify learners to provide targeted support.</p>
                  </div>
                  <div className={styles.serviceCard}>
                      <h4>Custom Learning Paths</h4>
                      <p>Unique study guides and pathways based on quiz performance.</p>
                  </div>
                </div>
              )}
            </li>
            <li className={styles.navItem}><Link to="/#about">About</Link></li>
          </ul>
          {isLoggedIn ? (
            <div 
              className={styles.profileIcon} 
              onClick={() => setPanelOpen(!panelOpen)}
            >
              {username.charAt(0)}
            </div>
          ) : (
            <Link to="/signup" className={styles.navButton}>Try It Free</Link>
          )}
        </div>
      </nav>

      {/* --- Slideout Panel for Logout --- */}
      {panelOpen && (
        <div className={styles.slidePanel}>
          <button className={styles.logoutButton} onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      )}
    </>
  );
};

export default Navbar;