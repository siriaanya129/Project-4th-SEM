// In frontend/src/components/PerformanceGraph.js

import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// We need to register the components we're using with Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const PerformanceGraph = ({ graphData }) => {

  // This is the data structure that Chart.js expects
  const data = {
    labels: graphData.labels, // The dates for the X-axis
    datasets: [
      {
        label: 'Accuracy Index',
        data: graphData.accuracy_index, // The data points for the first line
        borderColor: 'rgb(54, 162, 235)', // Blue color
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        tension: 0.1, // Makes the line slightly curved
      },
      {
        label: 'Efficiency Index',
        data: graphData.efficiency_index, // The data points for the second line
        borderColor: 'rgb(75, 192, 192)', // Green/Teal color
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.1,
      },
    ],
  };

  // Configuration options for the chart's appearance
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top', // Position the legend at the top
      },
      title: {
        display: false, // We already have a title on the page
      },
    },
    scales: {
        y: {
            beginAtZero: true, // Start the Y-axis at 0
            suggestedMax: 120 // Suggest a max value to give some headroom
        }
    }
  };

  return (
    <div style={{ position: 'relative', height: '400px' }}>
      <Line options={options} data={data} />
    </div>
  );
};

export default PerformanceGraph;