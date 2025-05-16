import React from "react";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  Title,
} from "chart.js";

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  Title,
);

interface ThreatTypeChartProps {
  data: { label: string; count: number }[];
  title?: string;
  className?: string;
}

export function ThreatTypeChart({
  data,
  title = "Threat Types Distribution",
  className = "",
}: ThreatTypeChartProps) {
  // Chart configuration
  const chartData = {
    labels: data.map((item) => item.label),
    datasets: [
      {
        data: data.map((item) => item.count),
        backgroundColor: [
          "rgba(255, 99, 132, 0.7)", // Red
          "rgba(54, 162, 235, 0.7)", // Blue
          "rgba(255, 206, 86, 0.7)", // Yellow
          "rgba(75, 192, 192, 0.7)", // Teal
          "rgba(153, 102, 255, 0.7)", // Purple
          "rgba(255, 159, 64, 0.7)", // Orange
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 206, 86, 1)",
          "rgba(75, 192, 192, 1)",
          "rgba(153, 102, 255, 1)",
          "rgba(255, 159, 64, 1)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "right" as const,
        labels: {
          color: "rgb(156, 163, 175)",
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: !!title,
        text: title,
        color: "rgb(156, 163, 175)",
        font: {
          size: 14,
          weight: "normal" as const,
        },
      },
      tooltip: {
        backgroundColor: "rgba(17, 24, 39, 0.8)",
        titleColor: "rgb(243, 244, 246)",
        bodyColor: "rgb(243, 244, 246)",
        bodyFont: {
          size: 13,
        },
        padding: 10,
        boxPadding: 6,
        callbacks: {
          label: function (context: any) {
            const label = context.label || "";
            const value = context.raw || 0;
            const total = context.chart.data.datasets[0].data.reduce(
              (a: number, b: number) => a + b,
              0,
            );
            const percentage = Math.round((value / total) * 100);
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div
      className={`relative bg-zinc-800 p-4 rounded-lg h-[300px] ${className}`}
    >
      <Pie data={chartData} options={options} />
    </div>
  );
}
