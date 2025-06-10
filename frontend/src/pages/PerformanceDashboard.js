import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './PerformanceDashboard.module.css';

const PerformanceDashboard = () => {
  // --- This original code is untouched ---
  const { subjectName } = useParams();
  const [timePeriod, setTimePeriod] = useState('all');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  // --- End of untouched original code ---

  // --- START OF NEW EDIT: Define the API URL ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF NEW EDIT ---

  // --- This original code is untouched ---
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setLoading(false);
        return;
      }
      
      try {
        // --- START OF NEW EDIT: Use API_URL ---
        const response = await fetch(`${API_URL}/api/v1/performance/dashboard?period=${timePeriod}`, {
        // --- END OF NEW EDIT ---
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setDashboardData(data);
        } else {
          console.error("Failed to fetch dashboard data.");
          setDashboardData(null);
        }
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      }
      setLoading(false);
    };

    fetchData();
  }, [timePeriod, API_URL]);

  const renderGridBox = (level, type) => {
    const data = dashboardData?.[level]?.[type];
    
    if (!data) {
        return <div className={styles.gridBox}><span className={styles.boxLabel}>{level} / {type}</span><span className={styles.boxScore}>0 / 0</span></div>;
    }

    const { total, correct } = data;
    const mistakes = total - correct;
    
    let boxStyle = styles.gridBox;
    if (total > 0) {
      const accuracy = (correct / total) * 100;
      if (accuracy < 50) boxStyle += ` ${styles.lowAccuracy}`;
      else if (accuracy < 80) boxStyle += ` ${styles.mediumAccuracy}`;
      else boxStyle += ` ${styles.highAccuracy}`;
    }

    return (
      <div className={boxStyle}>
        <span className={styles.boxLabel}>{level} / {type}</span>
        <span className={styles.boxScore}>{correct} / {total}</span>
        <span className={styles.boxMistakes}>{mistakes} mistake(s)</span>
      </div>
    );
  };

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.header}>
          <h1>Performance Dashboard</h1>
          <p>Your cumulative performance analytics for {subjectName}</p>
        </div>

        <div className={styles.filters}>
          <button onClick={() => setTimePeriod('1d')} className={timePeriod === '1d' ? styles.active : ''}>Last 24 Hours</button>
          <button onClick={() => setTimePeriod('7d')} className={timePeriod === '7d' ? styles.active : ''}>Last 7 Days</button>
          <button onClick={() => setTimePeriod('30d')} className={timePeriod === '30d' ? styles.active : ''}>Last 30 Days</button>
          <button onClick={() => setTimePeriod('all')} className={timePeriod === 'all' ? styles.active : ''}>All Time</button>
        </div>

        <div className={styles.content}>
          {loading ? (
            <p className={styles.loadingText}>Loading analytics...</p>
          ) : dashboardData ? (
            <div className={styles.dashboardGrid}>
              {renderGridBox('easy', 'direct')}
              {renderGridBox('easy', 'logical reasoning')}
              {renderGridBox('easy', 'aptitude')}
              
              {renderGridBox('medium', 'direct')}
              {renderGridBox('medium', 'logical reasoning')}
              {renderGridBox('medium', 'aptitude')}

              {renderGridBox('hard', 'direct')}
              {renderGridBox('hard', 'logical reasoning')}
              {renderGridBox('hard', 'aptitude')}
            </div>
          ) : (
            <p className={styles.loadingText}>No performance data available for the selected period.</p>
          )}

          <div className={styles.deepAnalysisContainer}>
            <Link to={`/subject/${subjectName}/deep-analysis`} className={styles.deepAnalysisButton}>
              More Deep Analysis
            </Link>
          </div>
        </div>
      </div>
    </>
  );
  // --- End of untouched original code ---
};

export default PerformanceDashboard;