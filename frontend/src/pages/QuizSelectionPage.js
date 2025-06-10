import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './QuizSelectionPage.module.css';

const QuizSelectionPage = () => {
  const { subjectName } = useParams();
  const [availability, setAvailability] = useState({ units: [], is_grand_quiz_locked: true });
  const [loading, setLoading] = useState(true);

  // --- START OF EDIT: Define API_URL ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF EDIT ---

  useEffect(() => {
    const fetchAvailability = async () => {
      setLoading(true);
      const token = localStorage.getItem('accessToken');
      if (!token) { setLoading(false); return; }

      try {
        // --- START OF EDIT: Use API_URL ---
        const response = await fetch(`${API_URL}/api/v1/quizzes/availability/${subjectName}`, {
        // --- END OF EDIT ---
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setAvailability(data);
        } else {
          console.error("Failed to get quiz data from server.");
        }
      } catch (error) {
        console.error("Failed to fetch quiz availability:", error);
      }
      setLoading(false);
    };

    fetchAvailability();
  }, [subjectName]);

  if (loading) {
    return <div className={styles.pageWrapper}><div className={styles.header}><h2>Loading...</h2></div></div>;
  }

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.header}>
          <h2>Choose Your Quiz</h2>
          <p>Select a unit quiz to begin, or take the Grand Quiz to test your overall knowledge.</p>
        </div>
        
        <div className={styles.quizListContainer}>
          {availability.units && availability.units.length > 0 ? (
            availability.units.map(unitName => (
              <Link key={unitName} to={`/quiz/welcome/unit/${encodeURIComponent(unitName)}`} className={styles.quizCard}>
                <span>Attempt Quiz:</span>
                <h3>{unitName}</h3>
              </Link>
            ))
          ) : (
            <div className={styles.noQuizzesMessage}>
              <p>No unit quizzes are available for this subject yet.</p>
            </div>
          )}

          <Link 
            to={availability.is_grand_quiz_locked ? '#' : `/quiz/welcome/grand/${subjectName}`} 
            className={`${styles.quizCard} ${styles.grandQuiz} ${availability.is_grand_quiz_locked ? styles.locked : ''}`}
            onClick={(e) => { if (availability.is_grand_quiz_locked) e.preventDefault(); }}
          >
            <span>Final Assessment</span>
            <h3>Grand Quiz</h3>
            {availability.is_grand_quiz_locked && <p className={styles.lockReason}>(Complete all unit quizzes to unlock)</p>}
          </Link>
        </div>
      </div>
    </>
  );
};

export default QuizSelectionPage;