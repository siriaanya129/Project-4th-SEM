// In frontend/src/pages/PreQuizPage.js
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './PreQuizPage.module.css';

const PreQuizPage = () => {
  const { type, name } = useParams();
  const isGrandQuiz = type === 'grand';

  // In a real app, you would fetch these topics from an API
  const topics = [
    "Describing data sets",
    "Sample Mean, Median, and Mode",
    "Sample Variance and Standard Deviation",
    "Percentiles and Box-plots"
  ];

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.contentCard}>
          <h1>{isGrandQuiz ? "Grand Quiz" : name}</h1>
          <p className={styles.subtitle}>
            {isGrandQuiz 
              ? "This is a comprehensive assessment covering all topics." 
              : "This quiz will cover the following key topics:"}
          </p>
          
          {!isGrandQuiz && (
            <ul className={styles.topicsList}>
              {topics.map(topic => <li key={topic}>{topic}</li>)}
            </ul>
          )}

          <div className={styles.instructions}>
             <p>You will have <strong>{isGrandQuiz ? '75 questions' : '15 questions'}</strong> to complete.</p>
            <p>Your time will be recorded to help analyze your performance speed.</p>
            <p>Please do your best and answer honestly. Good luck!</p>
          </div>

          <Link to={`/quiz/start/${type}/${name}`} className={styles.startButton}>
            Start Quiz
          </Link>
        </div>
      </div>
    </>
  );
};

export default PreQuizPage;