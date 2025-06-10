import React from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './SubjectPage.module.css';

const SubjectPage = () => {
  const { subjectName } = useParams();

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <section className={styles.heroSection}>
          <div className={styles.heroContent}>
            <h1>Welcome to the {subjectName} Course</h1>
            <p>Select an option below to begin your learning journey.</p>
          </div>
        </section>

        <section className={styles.contentSection}>
          <div className={styles.optionsGrid}>
            <Link to={`/subject/${subjectName}/quizzes`} className={styles.optionCard}>
              <h3>Attempt Quizzes</h3>
              <p>Test your knowledge with our dynamically generated quizzes.</p>
            </Link>
            
            <Link to={`/subject/${subjectName}/performance`} className={styles.optionCard}>
              <h3>Check Your Past Attempts</h3>
              <p>Review results and analysis from individual quiz attempts.</p>
            </Link>

            {/* --- START OF NEW CODE TO ADD --- */}
            {/* This is the new, third card for the dashboard. */}
            <Link to={`/subject/${subjectName}/dashboard`} className={styles.optionCard}>
              <h3>Performance Dashboard</h3>
              <p>View your cumulative analytics and progress over time.</p>
            </Link>
            {/* --- END OF NEW CODE TO ADD --- */}

            <Link to={`/subject/${subjectName}/materials`} className={styles.optionCard}>
              <h3>Study Materials</h3>
              <p>Access downloadable resources and study guides.</p>
            </Link>
            
          </div>
        </section>
      </div>
    </>
  );
};

export default SubjectPage;