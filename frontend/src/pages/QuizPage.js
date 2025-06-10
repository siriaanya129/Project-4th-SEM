import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './QuizPage.module.css';
import logo from '../assets/logo.png';

const QuizPage = () => {
  // --- This original code is untouched ---
  const { type, name } = useParams();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [timeTaken, setTimeTaken] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isFinished, setIsFinished] = useState(false);
  const [finalResult, setFinalResult] = useState(null);
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- End of untouched original code ---

  // --- START OF EDITED/CORRECTED CODE ---
  useEffect(() => {
    const fetchQuestions = async () => {
      // Get the token from browser storage
      const token = localStorage.getItem('accessToken');
      // If the user isn't logged in, we can't proceed. Redirect them.
      if (!token) {
        navigate('/login');
        return;
      }

      const encodedName = encodeURIComponent(name);
      const url = type === 'unit'
        ? `${API_URL}/api/v1/quiz/unit/${encodedName}`
        : `${API_URL}/api/v1/quiz/grand`;

      try {
        // THE FIX: Add the Authorization header to the fetch request
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setQuestions(data);
          let initialAnswers = {};
          data.forEach((q, index) => { initialAnswers[index] = null; });
          setSelectedAnswers(initialAnswers);
        } else {
          console.error("Failed to fetch questions. Status:", response.status);
          // If the token is expired or invalid, the server returns 401. Redirect to login.
          if (response.status === 401) {
            navigate('/login');
          }
        }
      } catch (error) {
        console.error("Failed to fetch questions:", error);
      }
      setIsLoading(false);
    };
    fetchQuestions();
  }, [type, name, navigate, API_URL]);
  // --- END OF EDITED/CORRECTED CODE ---

  // --- This original code is untouched ---
  useEffect(() => {
    if (isLoading || isFinished) return;
    const timerId = setInterval(() => {
      setTimeTaken(prevTime => prevTime + 1);
    }, 1000);
    return () => clearInterval(timerId);
  }, [isLoading, isFinished]);

  const handleSelectAnswer = (questionIndex, answerIndex) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionIndex]: answerIndex
    }));
  };

  const goToNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const goToPrev = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };
  
  const handleSubmit = useCallback(async () => {
      setIsFinished(true);
      const token = localStorage.getItem('accessToken');
      
      const payload = {
        quiz_questions: questions,
        student_answers: Object.values(selectedAnswers),
        time_taken_seconds: timeTaken
      };

      const endpoint =
        type === 'grand'
          ? `${API_URL}/api/v1/quiz/submit/grand`
          : `${API_URL}/api/v1/quiz/submit/unit`;

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        setFinalResult(result);
      } catch (error) {
        console.error("Failed to submit quiz:", error);
      }
  }, [questions, selectedAnswers, timeTaken, type, API_URL]);
  
  const formatTime = (totalSeconds) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  };

  if (isLoading) return <div className={styles.fullscreen}>Loading Quiz...</div>;
  if (!questions || questions.length === 0) return <div className={styles.fullscreen}>Could not load quiz questions. Please try again.</div>;

  const currentQuestion = questions[currentQuestionIndex];

  if (isFinished) {
    return (
        <div className={styles.fullscreen}>
            <div className={styles.resultsCard}>
                <h2>Quiz Complete!</h2>
                {finalResult ? (
                    <>
                        <h3>Your Score: {finalResult.total_score} / {finalResult.max_score}</h3>
                        <div className={styles.resultsBreakdown}>
                            {finalResult.detailed_results.map((res, index) => (
                                <div key={index} className={styles.resultItem}>
                                    <p><b>Q{index + 1}:</b> {res.question_text}</p>
                                    <p className={res.is_correct ? styles.correct : styles.incorrect}>
                                      Your Answer: {res.student_answer_index !== null ? questions[index].options[res.student_answer_index] : "Not Answered"}
                                    </p>
                                    {!res.is_correct && (
                                      <p className={styles.correct}>
                                        Correct Answer: {questions[index].options[res.correct_answer_index]}
                                      </p>
                                    )}
                                    <p className={styles.explanation}>
                                      <b>Explanation:</b> {questions[index].explanation || "No explanation available."}
                                    </p>
                                </div>
                            ))}
                        </div>
                        <button onClick={() => navigate('/subject/Statistics/quizzes')} className={styles.navButton}>Back to Quizzes</button>
                    </>
                ) : (
                    <p>Calculating results...</p>
                )}
            </div>
        </div>
    )
  }

  return (
    <div className={styles.fullscreen}>
      <div className={styles.quizContainer}>
        <div className={styles.quizHeader}>
          <img src={logo} alt="EduConnect Logo" className={styles.logo} />
          <div className={styles.timer}>{formatTime(timeTaken)}</div>
        </div>
        <div className={styles.progressIndicator}>
          <span>{String(currentQuestionIndex + 1).padStart(2, '0')}</span> / {String(questions.length).padStart(2, '0')}
        </div>
        <h3 className={styles.questionText}>{currentQuestion.question_text}</h3>
        <div className={styles.optionsList}>
          {currentQuestion.options.map((option, index) => (
            <button
              key={index}
              className={`${styles.optionButton} ${selectedAnswers[currentQuestionIndex] === index ? styles.selected : ''}`}
              onClick={() => handleSelectAnswer(currentQuestionIndex, index)}
            >
              {option}
            </button>
          ))}
        </div>
        <div className={styles.navigationButtons}>
          <button onClick={goToPrev} disabled={currentQuestionIndex === 0}>Prev</button>
          {currentQuestionIndex === questions.length - 1 ? (
            <button onClick={handleSubmit} className={styles.submitBtn}>Submit</button>
          ) : (
            <button onClick={goToNext}>Next</button>
          )}
        </div>
      </div>
    </div>
  );
  // --- End of untouched original code ---
};

export default QuizPage;