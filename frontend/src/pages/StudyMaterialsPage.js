import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import styles from './StudyMaterialsPage.module.css';

const StudyMaterialsPage = () => {
  // --- This original code is untouched ---
  const { subjectName } = useParams();
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  // --- End of untouched original code ---

  // --- START OF NEW EDIT: Define the API URL ---
  const API_URL = process.env.REACT_APP_API_BASE_URL || '';
  // --- END OF NEW EDIT ---

  // --- This original code is untouched ---
  useEffect(() => {
    const fetchMaterials = async () => {
      try {
        // --- START OF NEW EDIT: Use API_URL ---
        const response = await fetch(`${API_URL}/api/v1/materials/${subjectName}`);
        // --- END OF NEW EDIT ---
        if (response.ok) {
          const data = await response.json();
          setMaterials(data);
        }
      } catch (error) {
        console.error("Failed to fetch materials:", error);
      }
      setLoading(false);
    };
    fetchMaterials();
  }, [subjectName]);

  return (
    <>
      <Navbar />
      <div className={styles.pageWrapper}>
        <div className={styles.header}>
          <h2>Study Materials: {subjectName}</h2>
          <p>Downloadable resources to aid your learning.</p>
        </div>
        <div className={styles.materialsList}>
          {loading ? (
            <p>Loading materials...</p>
          ) : materials.length > 0 ? (
            materials.map((material, index) => {
              const fileName = material.url.split('/').pop();
              return (
                <Link 
                  key={index} 
                  to={`/subject/${subjectName}/materials/${encodeURIComponent(fileName)}`}
                  className={styles.materialItem}
                >
                  <h3>{material.name}</h3>
                  <span>Click to View</span>
                </Link>
              )
            })
          ) : (
            <p>No study materials are available for this subject yet.</p>
          )}
        </div>
      </div>
    </>
  );
  // --- End of untouched original code ---
};

export default StudyMaterialsPage;