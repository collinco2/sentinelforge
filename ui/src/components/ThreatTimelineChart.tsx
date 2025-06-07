import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

// Register required chart components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

// Define the data structure
export interface TimelineDataPoint {
  date: string;
  count: number;
}

interface ThreatTimelineChartProps {
  data: TimelineDataPoint[];
  title?: string;
  className?: string;
  height?: number;
}

export function ThreatTimelineChart({ 
  data, 
  title = 'IOC Activity Timeline', 
  className = '',
  height = 300
}: ThreatTimelineChartProps) {
  
  // Format dates for display and sort chronologically
  const sortedData = [...data].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const chartData = {
    labels: sortedData.map(point => formatDate(point.date)),
    datasets: [
      {
        label: 'IOC Observations',
        data: sortedData.map(point => point.count),
        borderColor: 'rgba(59, 130, 246, 1)', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointBorderColor: '#fff',
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.2, // Slight curve to lines
      }
    ]
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          color: 'rgba(156, 163, 175, 1)', // gray-400
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(24, 24, 27, 0.9)', // zinc-900 with opacity
        titleColor: 'rgba(255, 255, 255, 0.9)',
        bodyColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: 'rgba(63, 63, 70, 1)', // zinc-700
        borderWidth: 1,
        padding: 10,
        displayColors: false,
        callbacks: {
          title: (tooltipItems) => {
            const index = tooltipItems[0].dataIndex;
            return `Date: ${sortedData[index]?.date}`;
          },
          label: (tooltipItem) => {
            return `Count: ${tooltipItem.raw}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(63, 63, 70, 0.3)', // zinc-700 with opacity
        },
        ticks: {
          color: 'rgba(156, 163, 175, 1)', // gray-400
          font: {
            size: 10
          },
          maxRotation: 45,
          minRotation: 45
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(63, 63, 70, 0.3)', // zinc-700 with opacity
        },
        ticks: {
          color: 'rgba(156, 163, 175, 1)', // gray-400
          precision: 0, // Only show integers
          font: {
            size: 11
          }
        }
      }
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    animations: {
      tension: {
        duration: 1000,
        easing: 'linear',
        from: 0.2,
        to: 0.2,
      }
    }
  };

  return (
    <div className={className}>
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      <div style={{ height: `${height}px` }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

// Helper to format dates for display
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  });
} 