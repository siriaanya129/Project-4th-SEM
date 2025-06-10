// In frontend/src/pages/DeepAnalysisPage.js

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './DeepAnalysisPage.module.css';
import PerformanceGraph from '../components/PerformanceGraph';
import LearningPathway from '../components/LearningPathway';

const DeepAnalysisPage = () => {
  // --- This original code is untouched ---
  const { subjectName } = useParams();
  const [timePeriod, setTimePeriod] = useState('all');
  const [graphData, setGraphData] = useState(null);
  const [loadingGraph, setLoadingGraph] = useState(true);
  const [pathwayData, setPathwayData] = useState(null);
  const [loadingPathway, setLoadingPathway] = useState(false);
  const [userCategory, setUserCategory] = useState(null);
  // --- End of untouched original code ---

  // --- START OF NEW EDIT: Define the API URL ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF NEW EDIT ---

  // --- This original code is untouched ---
  useEffect(() => {
    const fetchGraphData = async () => {
      setLoadingGraph(true);
      const token = localStorage.getItem('accessToken');
      if (!token) { setLoadingGraph(false); return; }
      
      try {
        // --- START OF NEW EDIT: Use API_URL ---
        const response = await fetch(`${API_URL}/api/v1/dashboard/graph-data?period=${timePeriod}`, {
        // --- END OF NEW EDIT ---
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setGraphData(data);
        } else { setGraphData(null); }
      } catch (error) { console.error("Error fetching graph data:", error); }
      setLoadingGraph(false);
    };

    fetchGraphData();
  }, [timePeriod]);

  const handleGeneratePathway = async () => {
    setLoadingPathway(true);
    const token = localStorage.getItem('accessToken');
    try {
      // --- START OF NEW EDIT: Use API_URL ---
      const response = await fetch(`${API_URL}/api/v1/dashboard/generate-pathway`, {
      // --- END OF NEW EDIT ---
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        console.log("Learning Pathway API response:", data);
        setPathwayData(data);
        setUserCategory(data.user_category);
      } else {
        console.error("Failed to generate learning pathway.");
      }
    } catch (error) {
      console.error("Error generating learning pathway:", error);
    }
    setLoadingPathway(false);
  };
  // --- End of untouched original code ---

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.header}>
          <h1>Deep Performance Analysis</h1>
          <p>Analyzing your cumulative progress in {subjectName}</p>
        </div>

        <div className={styles.filters}>
          <button onClick={() => setTimePeriod('7d')} className={timePeriod === '7d' ? styles.active : ''}>Last 7 Days</button>
          <button onClick={() => setTimePeriod('30d')} className={timePeriod === '30d' ? styles.active : ''}>Last 30 Days</button>
          <button onClick={() => setTimePeriod('all')} className={timePeriod === 'all' ? styles.active : ''}>All Time</button>
        </div>

        <div className={styles.content}>
          <div className={styles.section}>
            <h2>Performance Over Time</h2>
            {userCategory && (
              <p className={styles.categoryText}>
                You are categorized as a <strong>{userCategory}</strong>
              </p>
            )}
            {loadingGraph ? (
              <p className={styles.loadingText}>Loading graph...</p>
            ) : graphData && graphData.labels.length > 0 ? (
              <PerformanceGraph graphData={graphData} />
            ) : (
              <p className={styles.loadingText}>No performance data available for the selected period.</p>
            )}
          </div>
          
          <div className={styles.pathwaySection}>
            <button 
              onClick={handleGeneratePathway} 
              className={styles.pathwayButton}
              disabled={loadingPathway}
            >
              {loadingPathway ? 'Generating...' : 'Generate Learning Pathway'}
            </button>
            {pathwayData && (
              <div className={styles.pathwayResult}>
                <LearningPathway pathwayData={pathwayData} />
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
  // --- End of untouched original code ---
};

export default DeepAnalysisPage;