import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import MarkdownIt from "markdown-it";
import { saveAs } from "file-saver";
import { IOCData } from "../components/IocTable";
import { IocDetailData } from "../hooks/useIocDetail";

const md = new MarkdownIt();

/**
 * Format timestamp to a readable format
 */
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (e) {
    return timestamp;
  }
};

/**
 * Convert severity to an emoji for visual representation
 */
const getSeverityEmoji = (severity: string): string => {
  switch (severity) {
    case "critical":
      return "🔴";
    case "high":
      return "🟠";
    case "medium":
      return "🟡";
    case "low":
      return "🔵";
    default:
      return "⚪";
  }
};

/**
 * Generate a markdown report for a single IOC
 */
export const generateIocMarkdown = (ioc: IocDetailData | IOCData): string => {
  const markdownContent = [];

  // Header
  markdownContent.push(`# IOC Report: ${ioc.value}`);
  markdownContent.push(`\n*Generated on ${new Date().toLocaleString()}*\n`);

  // Basic info
  markdownContent.push(`## Basic Information`);
  markdownContent.push(`- **Value:** \`${ioc.value}\``);
  markdownContent.push(`- **Type:** ${ioc.type}`);
  markdownContent.push(
    `- **Severity:** ${getSeverityEmoji(ioc.severity)} ${ioc.severity.toUpperCase()}`,
  );
  markdownContent.push(`- **Confidence:** ${ioc.confidence}%`);
  markdownContent.push(
    `- **First Observed:** ${formatTimestamp(ioc.first_observed || ioc.timestamp)}`,
  );

  if ("last_seen" in ioc && ioc.last_seen) {
    markdownContent.push(`- **Last Seen:** ${formatTimestamp(ioc.last_seen)}`);
  }

  // Scoring rationale if available
  if ("scoring_rationale" in ioc && ioc.scoring_rationale) {
    markdownContent.push(`\n## Scoring Rationale`);
    markdownContent.push(`### Factors`);

    ioc.scoring_rationale.factors.forEach((factor) => {
      markdownContent.push(
        `- **${factor.name}:** ${(factor.weight * 100).toFixed(0)}%${factor.description ? ` - ${factor.description}` : ""}`,
      );
    });

    if (ioc.scoring_rationale.model_version) {
      markdownContent.push(
        `\n*Model Version: ${ioc.scoring_rationale.model_version}*`,
      );
    }
  }

  // MITRE ATT&CK data if available
  if (
    "mitre_techniques" in ioc &&
    ioc.mitre_techniques &&
    ioc.mitre_techniques.length > 0
  ) {
    markdownContent.push(`\n## MITRE ATT&CK Techniques`);
    ioc.mitre_techniques.forEach((technique) => {
      markdownContent.push(
        `- **${technique.id}:** ${technique.name} (${technique.confidence} confidence)`,
      );
    });
  }

  if (
    "mitre_tactics" in ioc &&
    ioc.mitre_tactics &&
    ioc.mitre_tactics.length > 0
  ) {
    markdownContent.push(`\n## MITRE ATT&CK Tactics`);
    ioc.mitre_tactics.forEach((tactic) => {
      markdownContent.push(`- ${tactic.name}`);
    });
  }

  // Alerts if available
  if ("alerts" in ioc && ioc.alerts && ioc.alerts.length > 0) {
    markdownContent.push(`\n## Associated Alerts`);
    ioc.alerts.forEach((alert) => {
      markdownContent.push(`- **${alert.name}** - ${alert.timestamp}`);
    });
  }

  return markdownContent.join("\n");
};

/**
 * Generate markdown for multiple IOCs
 */
export const generateIocsListMarkdown = (
  iocs: IOCData[],
  title: string = "IOCs Report",
): string => {
  const markdownContent = [];

  // Header
  markdownContent.push(`# ${title}`);
  markdownContent.push(`\n*Generated on ${new Date().toLocaleString()}*\n`);
  markdownContent.push(`*Total IOCs: ${iocs.length}*\n`);

  // Table header
  markdownContent.push(
    "| IOC Value | Type | Severity | Confidence | First Observed |",
  );
  markdownContent.push(
    "|-----------|------|----------|------------|----------------|",
  );

  // Table rows
  iocs.forEach((ioc) => {
    markdownContent.push(
      `| \`${ioc.value}\` | ${ioc.type} | ${getSeverityEmoji(ioc.severity)} ${ioc.severity} | ${ioc.confidence}% | ${formatTimestamp(ioc.timestamp)} |`,
    );
  });

  // Add statistics
  const severityCounts = iocs.reduce(
    (acc, ioc) => {
      acc[ioc.severity] = (acc[ioc.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const typeCounts = iocs.reduce(
    (acc, ioc) => {
      acc[ioc.type] = (acc[ioc.type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  markdownContent.push("\n## Summary Statistics");

  markdownContent.push("\n### Severity Distribution");
  for (const [severity, count] of Object.entries(severityCounts)) {
    markdownContent.push(
      `- **${severity}:** ${count} (${((count / iocs.length) * 100).toFixed(1)}%)`,
    );
  }

  markdownContent.push("\n### Type Distribution");
  for (const [type, count] of Object.entries(typeCounts)) {
    markdownContent.push(
      `- **${type}:** ${count} (${((count / iocs.length) * 100).toFixed(1)}%)`,
    );
  }

  return markdownContent.join("\n");
};

/**
 * Export markdown content to a file
 */
export const exportMarkdown = (
  markdownContent: string,
  filename: string,
): void => {
  const blob = new Blob([markdownContent], {
    type: "text/markdown;charset=utf-8",
  });
  saveAs(blob, `${filename}.md`);
};

/**
 * Create a PDF from HTML content
 */
const createPdfFromHtml = async (
  contentElement: HTMLElement,
  filename: string,
  orientation: "portrait" | "landscape" = "portrait",
): Promise<void> => {
  try {
    // Capture the HTML content as a canvas
    const canvas = await html2canvas(contentElement, {
      scale: 2, // Higher scale for better quality
      logging: false,
      useCORS: true,
    });

    // Create PDF with appropriate dimensions
    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF({
      orientation,
      unit: "mm",
    });

    const imgWidth = orientation === "portrait" ? 210 : 297;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    pdf.addImage(imgData, "PNG", 0, 0, imgWidth, imgHeight);
    pdf.save(`${filename}.pdf`);
  } catch (error) {
    console.error("Error generating PDF:", error);
    throw error;
  }
};

/**
 * Convert markdown to HTML for PDF generation
 */
const markdownToHtml = (markdownContent: string): string => {
  const renderedHtml = md.render(markdownContent);

  // Add CSS styling for the PDF
  return `
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto;">
      ${renderedHtml}
    </div>
  `;
};

/**
 * Export IOC data as PDF
 */
export const exportAsPdf = async (
  content: IOCData | IocDetailData | IOCData[],
  title: string = "IOC Report",
): Promise<void> => {
  let markdownContent: string;
  let filename: string;

  if (Array.isArray(content)) {
    markdownContent = generateIocsListMarkdown(content, title);
    filename = "iocs-report";
  } else {
    markdownContent = generateIocMarkdown(content);
    filename = `ioc-${content.id || content.value.substring(0, 10)}-report`;
  }

  // Create temporary element to render HTML
  const tempDiv = document.createElement("div");
  tempDiv.style.position = "absolute";
  tempDiv.style.left = "-9999px";
  tempDiv.style.top = "-9999px";
  tempDiv.innerHTML = markdownToHtml(markdownContent);
  document.body.appendChild(tempDiv);

  try {
    await createPdfFromHtml(
      tempDiv,
      filename,
      Array.isArray(content) ? "landscape" : "portrait",
    );
  } finally {
    // Cleanup
    document.body.removeChild(tempDiv);
  }
};

/**
 * Export options type
 */
export type ExportFormat = "pdf" | "markdown";
export type ExportScope = "single" | "visible" | "all";

/**
 * Export IOC data in the specified format
 */
export const exportIocData = async (
  data: IOCData | IocDetailData | IOCData[],
  format: ExportFormat = "pdf",
  title: string = "IOC Report",
): Promise<void> => {
  const isSingle = !Array.isArray(data);
  const filename = isSingle
    ? `ioc-${(data as IOCData).id || (data as IOCData).value.substring(0, 10)}-report`
    : "iocs-report";

  try {
    if (format === "pdf") {
      await exportAsPdf(data, title);
    } else {
      // Markdown export
      const markdownContent = isSingle
        ? generateIocMarkdown(data as IOCData | IocDetailData)
        : generateIocsListMarkdown(data as IOCData[], title);

      exportMarkdown(markdownContent, filename);
    }
  } catch (error) {
    console.error(`Error exporting as ${format}:`, error);
    throw error;
  }
};
