import React, { useState } from 'react';
import styles from './LearningPathway.module.css';

const LearningPathway = ({ pathwayData }) => {
  const [openUnit, setOpenUnit] = useState(null);
  const [openTopic, setOpenTopic] = useState(null);

 if (
  !pathwayData ||
  !Array.isArray(pathwayData.learning_path) ||
  pathwayData.learning_path.length === 0
 ) {
  return <p className={styles.noPathMessage}>No weaknesses found! Keep up the great work!</p>;
   } 

  const handleUnitClick = (unitName) => {
    setOpenUnit(prev => (prev === unitName ? null : unitName));
    setOpenTopic(null); // Close topics when collapsing a unit
  };
  
  const handleTopicClick = (topicName) => {
    setOpenTopic(prev => (prev === topicName ? null : topicName));
  };

  return (
    <div className={styles.pathwayContainer}>
      <div className={styles.pathwayHeader}>
        <h3>Your Personalized Learning Pathway</h3>
        <p>Focus on your weakest areas first. Expand each level to see what you need to study.</p>
        <div className={styles.category}>
          You are currently categorized as a: <strong>{pathwayData.user_category}</strong>
        </div>
      </div>
      
      <div className={styles.pathwayTree}>
        <div className={styles.rootNode}>Statistics</div>
        <div className={styles.horizontalConnector}></div>
        
        <div className={styles.unitsContainer}>
          {pathwayData.learning_path.map((unitItem) => (
            <div key={unitItem.unit} className={styles.unitBranch}>
              <div className={styles.verticalConnector}></div>
              <div className={styles.unitNode} onClick={() => handleUnitClick(unitItem.unit)}>
                <span className={styles.nodeTitle}>{unitItem.unit}</span>
              </div>
              
              {openUnit === unitItem.unit && (
                <div className={styles.topicsContainer}>
                  {unitItem.topics.map((topicItem) => (
                    <div key={topicItem.topic}>
                      <div className={styles.topicNode} onClick={() => handleTopicClick(topicItem.topic)}>
                        <span className={styles.nodeTitle}>{topicItem.topic}</span>
                      </div>
                      
                      {openTopic === topicItem.topic && (
                        <div className={styles.subtopicsContainer}>
                          {topicItem.subtopics.map((subtopicItem) => (
                            <div 
                              key={subtopicItem.subtopic}
                              className={`${styles.subtopicNode} ${styles[subtopicItem.status.replace(" ", "-").toLowerCase()]}`}
                            >
                              {subtopicItem.subtopic}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LearningPathway;