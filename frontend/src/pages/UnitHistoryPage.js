import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import AnalysisModal from '../components/AnalysisModal';
import styles from './PerformancePage.module.css';

const formatTimestamp = (isoString) => {
  if (!isoString) return "Invalid Date";
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "Invalid Date";
  return date.toLocaleString('en-US', { 
    year: 'numeric', month: 'long', day: 'numeric', 
    hour: '2-digit', minute: '2-digit' 
  });
};

const UnitHistoryPage = () => {
  // --- This original code is untouched ---
  const { subjectName, unitName } = useParams();
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedAttempt, setSelectedAttempt] = useState(null);
  // --- End of untouched original code ---

  // --- START OF NEW EDIT: Define the API URL ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF NEW EDIT ---

  // --- This original code is untouched ---
  useEffect(() => {
    const fetchAttempts = async () => {
      const token = localStorage.getItem('accessToken');
      const decodedUnitName = decodeURIComponent(unitName);

      try {
        // --- START OF NEW EDIT: Use API_URL ---
        const response = await fetch(`${API_URL}/api/v1/performance/history/${decodedUnitName}`, {
        // --- END OF NEW EDIT ---
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setAttempts(data);
        }
      } catch (error) {
        console.error("Failed to fetch unit history:", error);
      }
      setLoading(false);
    };

    fetchAttempts();
  }, [unitName]);

  const handleCardClick = (attemptData) => {
    setSelectedAttempt(attemptData);
    setModalOpen(true);
  };

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.header}>
          <h2>Attempt History for:</h2>
          <h3>{decodeURIComponent(unitName)}</h3>
        </div>
        <div className={styles.historyList}>
          {loading ? <p>Loading history...</p> : 
           attempts.length > 0 ? (
            attempts.map((attempt, index) => (
              <div key={index} className={styles.historyCard} onClick={() => handleCardClick(attempt)}>
                <h3>Attempt on: {formatTimestamp(attempt.timestamp)}</h3>
                <p>Click to view details and analyze</p>
              </div>
            ))
          ) : (
            <p>You have not attempted this quiz yet.</p>
          )}
        </div>
      </div>
      <AnalysisModal 
        isOpen={isModalOpen} 
        onClose={() => setModalOpen(false)}
        quizData={selectedAttempt}
      />
    </>
  );
  // --- End of untouched original code ---
};

export default UnitHistoryPage;