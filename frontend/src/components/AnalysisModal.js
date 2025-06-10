import React, { useState, useEffect } from 'react';
import styles from './AnalysisModal.module.css';

const AnalysisModal = ({ isOpen, onClose, quizData }) => {
  // --- START OF NEW CODE TO ADD ---
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState(null);

  // This hook ensures that when you open the modal for a new quiz,
  // the old analysis data is cleared away.
  useEffect(() => {
    if (isOpen) {
      setAnalysisResult(null);
      setSelectedTopic(null);
    }
  }, [isOpen]);
  // --- END OF NEW CODE TO ADD ---

  if (!isOpen || !quizData) {
    return null;
  }

  // This is your existing, working data extraction logic. It is unchanged.
  const scoring = quizData.scoring_summary || {};
  const performance = quizData.performance_breakdown || [];
  const timeTaken = quizData.time_taken_seconds ?? null;

  const score = scoring.total_score ?? 'N/A';
  const maxScore = scoring.max_score ?? 'N/A';
  const correctQuestions = scoring.correct_answers_count ?? performance.filter(q => q.is_correct).length;
  const totalQuestions = scoring.total_questions ?? performance.length;
  const incorrectQuestions = totalQuestions - correctQuestions;

  const difficultyBreakdown = scoring.difficulty_breakdown || {};
  const typeBreakdown = scoring.type_breakdown || {};
  const topics = scoring.topics_covered || [];

  // --- START OF NEW CODE TO ADD ---
  // This replaces your simple alert() with the real API call logic.
  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setSelectedTopic(null);
    const token = localStorage.getItem('accessToken');
    try {
      const response = await fetch('http://localhost:8000/api/v1/performance/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ performance_breakdown: performance })
      });
      if (response.ok) {
        const data = await response.json();
        setAnalysisResult(data);
      } else {
        console.error("Analysis request failed");
      }
    } catch (error) {
      console.error("Error during analysis:", error);
    }
    setIsAnalyzing(false);
  };

  // This is a new helper function to handle clicking on a topic card.
  const handleTopicClick = (topicName) => {
    setSelectedTopic(prev => (prev === topicName ? null : topicName));
  };
  // --- END OF NEW CODE TO ADD ---

  const formatTime = (seconds) => {
    if (!seconds || typeof seconds !== 'number') return "N/A";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>Analysis for: {quizData.quiz_name}</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>
        <div className={styles.modalBody}>
          <div className={styles.statsGrid}>
            <div className={styles.statBox}>
              <h4>Score</h4>
              <p>{score} / {maxScore}</p>
            </div>
            <div className={styles.statBox}>
              <h4>Correct Answers</h4>
              <p>{correctQuestions}</p>
            </div>
            <div className={styles.statBox}>
              <h4>Incorrect Answers</h4>
              <p>{incorrectQuestions}</p>
            </div>
            <div className={styles.statBox}>
              <h4>Time Taken</h4>
              <p>{formatTime(timeTaken)}</p>
            </div>
          </div>

          <div className={styles.breakdownSection}>
            <h4>Difficulty Breakdown</h4>
            <ul>
              {Object.entries(difficultyBreakdown).map(([level, count]) => (
                <li key={level}>{level}: {count}</li>
              ))}
            </ul>
            <h4>Type Breakdown</h4>
            <ul>
              {Object.entries(typeBreakdown).map(([type, count]) => (
                <li key={type}>{type}: {count}</li>
              ))}
            </ul>
            <h4>Topics Covered</h4>
            <ul>
              {topics.map((topic, idx) => <li key={idx}>{topic}</li>)}
            </ul>
          </div>

          {/* This is the div you wanted updated. It now contains the new logic. */}
          <div className={styles.analysisSection}>
            {/* --- START OF NEW CODE TO ADD --- */}
            {!analysisResult ? (
              <div className={styles.placeholder}>
                <p>Click "Analyze Performance" to see a detailed breakdown by topic.</p>
              </div>
            ) : (
              <div className={styles.topicsContainer}>
                {Object.entries(analysisResult).map(([topic, subtopicData]) => {
                  const totalInTopic = Object.values(subtopicData).reduce((sum, s) => sum + s.total, 0);
                  const correctInTopic = Object.values(subtopicData).reduce((sum, s) => sum + s.correct, 0);
                  const isWeakTopic = correctInTopic < totalInTopic;

                  return (
                    <div key={topic}>
                      <div 
                        className={`${styles.topicCard} ${isWeakTopic ? styles.weak : ''}`}
                        onClick={() => handleTopicClick(topic)}
                      >
                        <span>{topic}</span>
                        <span>{correctInTopic} / {totalInTopic}</span>
                      </div>
                      
                      {selectedTopic === topic && (
                         <div className={styles.subtopicsContainer}>
                          {Object.entries(subtopicData).map(([subtopicName, counts]) => {
                            const isSubtopicWeak = counts.correct < counts.total;
                            return (
                              <div 
                                key={subtopicName} 
                                className={`${styles.subtopicCard} ${isSubtopicWeak ? styles.weak : ''}`}
                              >
                                <span>{subtopicName}</span>
                                <span>{counts.correct} / {counts.total}</span>
                              </div>
                            );
                          })}
                         </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            {/* --- END OF NEW CODE TO ADD --- */}
          </div>
        </div>
        <div className={styles.modalFooter}>
          {/* --- START OF EDIT: Update button to be interactive --- */}
          <button onClick={handleAnalyze} className={styles.analyzeButton} disabled={isAnalyzing}>
            {isAnalyzing ? 'Analyzing...' : 'Analyze Performance'}
          </button>
          {/* --- END OF EDIT --- */}
        </div>
      </div>
    </div>
  );
};

export default AnalysisModal;