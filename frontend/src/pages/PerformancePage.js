import React from 'react';
import { Link, useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './PerformancePage.module.css'; // We will reuse these styles

const PerformancePage = () => {
  const { subjectName } = useParams();

  // For now, we statically know the units. We can fetch them if needed later.
  const units = [
    "Unit-I Descriptive Statistics",
    "Unit-II Sampling and Distributions",
    "Unit-III Correlation, Covariance and Independent Random Variables",
    "Unit-IV Large Sample Estimation",
    "Unit-V Hypothesis Testing"
  ];

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.header}>
          <h2>Performance Overview</h2>
          <p>Select a unit to review your past attempts.</p>
        </div>

        <div className={styles.historyList}>
          {units.map((unitName, index) => (
            <Link
              key={index}
              to={`/subject/${subjectName}/performance/${encodeURIComponent(unitName)}`}
              className={styles.historyCard}
            >
              <h3>{unitName}</h3>
              <p>View all attempts for this unit</p>
            </Link>
          ))}

          {/* ✅ Added Grand Quiz card properly outside the map */}
          <Link
            to={`/subject/${subjectName}/performance/Grand Quiz`}
            className={styles.historyCard}
          >
            <h3>Grand Quiz</h3>
            <p>View all attempts for Grand Quiz</p>
          </Link>
        </div>
      </div>
    </>
  );
};

export default PerformancePage;
