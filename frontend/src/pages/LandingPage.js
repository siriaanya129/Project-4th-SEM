import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './LandingPage.module.css';
import useAuth from '../hooks/useAuth';

const LandingPage = () => {
  const { isLoggedIn } = useAuth();

  return (
    <>
      <Navbar />
      {/* This main wrapper correctly applies different background styles based on login state */}
      <div className={`${styles.pageWrapper} ${isLoggedIn ? styles.loggedIn : styles.loggedOut}`}>
        <section className={styles.heroSection}>
          <div className={styles.heroContent}>
            
            {/* This is the TERNARY OPERATOR that switches the content */}
            {isLoggedIn ? (
              // --- AFTER LOGIN ---
              <>
                <h1>Select a Subject to Begin</h1>
                <div className={styles.subjectsGrid}>
                  <Link to="/subject/Statistics" className={styles.subjectCard}>
                    <h4>Statistics</h4>
                  </Link>
                  <div className={`${styles.subjectCard} ${styles.disabled}`}>
                    <h4>Design & Analysis of Algorithms</h4>
                    <span>(Coming Soon)</span>
                  </div>
                  <div className={`${styles.subjectCard} ${styles.disabled}`}>
                    <h4>AIML</h4>
                    <span>(Coming Soon)</span>
                  </div>
                  <div className={`${styles.subjectCard} ${styles.disabled}`}>
                    <h4>Computer Networks</h4>
                    <span>(Coming Soon)</span>
                  </div>
                </div>
              </>
            ) : (
              // --- BEFORE LOGIN (The Corrected Part) ---
              <>
                <h1>We help students learn with personalized paths</h1>
                <p className={styles.heroSubtitle}>
                  Our platform uses dynamically generated quizzes and advanced analytics to create a learning experience tailored just for you. Start your journey to academic excellence today.
                </p>
                <Link to="/signup" className={styles.heroButton}>Get Started</Link>
              </>
            )}

          </div>
        </section>
      </div>
    </>
  );
};

export default LandingPage;