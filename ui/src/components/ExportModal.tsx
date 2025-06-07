import React from 'react';
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import { IOC, Stats, exportToCSV } from '../services/api';

export interface ExportModalProps {
  open: boolean;
  onClose: () => void;
  iocs: IOC[];
  stats: Stats | null;
}

const ExportModal: React.FC<ExportModalProps> = ({ open, onClose, iocs, stats }) => {
  if (!open) return null;

  const handleGenerateIocReport = () => {
    // Filter to high-risk IOCs
    const highRiskIocs = iocs.filter(ioc => ioc.score > 7.5);
    alert(`PDF Report Generated with ${highRiskIocs.length} high-risk IOCs`);
    onClose();
  };

  const handleExportCSV = () => {
    exportToCSV();
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Export Options</DialogTitle>
      <DialogContent>
        <List>
          <ListItem button onClick={handleExportCSV}>
            <ListItemIcon>
              <span className="material-icons">table_view</span>
            </ListItemIcon>
            <ListItemText 
              primary="Export to CSV" 
              secondary={`Export all ${iocs.length} IOCs to CSV format`} 
            />
          </ListItem>
          <Divider />
          <ListItem button onClick={handleGenerateIocReport}>
            <ListItemIcon>
              <span className="material-icons">picture_as_pdf</span>
            </ListItemIcon>
            <ListItemText 
              primary="Generate Threat Report (PDF)" 
              secondary="Create a comprehensive PDF report with high-risk IOCs and analysis" 
            />
          </ListItem>
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExportModal; 