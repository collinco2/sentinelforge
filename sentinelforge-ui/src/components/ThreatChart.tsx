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
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { cn } from '../lib/utils';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Chart options
const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: '#A1A1AA' // text-gray-400
      }
    },
    title: {
      display: false,
    },
    tooltip: {
      backgroundColor: '#18181B', // bg-zinc-900
      borderColor: '#3F3F46', // border-zinc-700
      borderWidth: 1,
      titleColor: '#E4E4E7', // text-zinc-200
      bodyColor: '#A1A1AA', // text-gray-400
      padding: 10,
    }
  },
  scales: {
    x: {
      grid: {
        color: '#3F3F46', // border-zinc-700
        drawBorder: false,
      },
      ticks: {
        color: '#71717A', // text-zinc-500
      }
    },
    y: {
      grid: {
        color: '#3F3F46', // border-zinc-700
        drawBorder: false,
      },
      ticks: {
        color: '#71717A', // text-zinc-500
      }
    }
  },
};

// Mock data for the last 7 days
const labels = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'];

const mockThreatData = {
  labels,
  datasets: [
    {
      label: 'Critical Threats',
      data: [12, 19, 8, 15, 12, 23, 17],
      borderColor: '#EF4444', // text-red-500
      backgroundColor: 'rgba(239, 68, 68, 0.5)', // text-red-500 with opacity
      tension: 0.3,
    },
    {
      label: 'High Severity',
      data: [7, 11, 15, 23, 18, 25, 31],
      borderColor: '#F97316', // text-orange-500
      backgroundColor: 'rgba(249, 115, 22, 0.5)', // text-orange-500 with opacity
      tension: 0.3,
    },
    {
      label: 'Medium Severity',
      data: [15, 22, 28, 33, 29, 35, 40],
      borderColor: '#EAB308', // text-yellow-500
      backgroundColor: 'rgba(234, 179, 8, 0.5)', // text-yellow-500 with opacity
      tension: 0.3,
    },
  ],
};

interface ThreatChartProps {
  className?: string;
}

export function ThreatChart({ className }: ThreatChartProps) {
  return (
    <div className={cn('w-full h-full', className)}>
      <Line options={options} data={mockThreatData} />
    </div>
  );
} 