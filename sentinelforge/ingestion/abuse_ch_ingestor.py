import csv
import requests
import logging
from datetime import datetime

# Corrected import path
from .threat_intel_ingestor import ThreatIntelIngestor

logger = logging.getLogger(__name__)

class AbuseChIngestor(ThreatIntelIngestor):
    """
    Pull malware data from Abuse.ch Feodo Tracker.
    https://feodotracker.abuse.ch/
    """

    def __init__(self):
        # Supported feeds from Abuse.ch
        self.feeds = {
            "ip_blocklist": "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
            "malware_hashes": "https://bazaar.abuse.ch/export/csv/recent/",
        }

    # Adjusted method signature to match the base class abstract method
    def get_indicators(self, source_url: str = None) -> list[dict]:
        indicators = []
        
        # Process IP blocklist
        ip_indicators = self._get_ip_blocklist()
        indicators.extend(ip_indicators)
        
        # Process malware hashes
        hash_indicators = self._get_malware_hashes()
        indicators.extend(hash_indicators)
        
        logger.info(f"AbuseChIngestor extracted {len(indicators)} total indicators")
        return indicators
    
    def _get_ip_blocklist(self) -> list[dict]:
        """Process the IP blocklist feed"""
        url = self.feeds["ip_blocklist"]
        indicators = []
        
        try:
            logger.info(f"Fetching IP blocklist from {url}")
            r = requests.get(url)
            r.raise_for_status()

            # Filter out comment lines
            lines = [
                line
                for line in r.text.splitlines()
                if not line.strip().startswith("#")
            ]

            if not lines:
                return []
                
            # Skip header
            reader = csv.reader(lines[1:])
            
            for row in reader:
                if row and len(row) > 0:
                    ip = row[0].strip()
                    
                    indicator = {
                        "ip": ip,
                        "type": "ip",
                        "description": "Feodo Tracker Botnet C2 IP"
                    }
                    
                    # Add extra data if available
                    if len(row) > 1:
                        indicator["malware_family"] = row[1].strip()
                        
                    if len(row) > 2:
                        indicator["status"] = row[2].strip()
                    
                    indicators.append(indicator)
                    
            logger.info(f"Extracted {len(indicators)} IP indicators from Feodo Tracker")
            
        except Exception as e:
            logger.error(f"Error fetching/parsing Feodo Tracker IP list: {e}")
            
        return indicators
    
    def _get_malware_hashes(self) -> list[dict]:
        """Process the malware hash feed"""
        url = self.feeds["malware_hashes"]
        indicators = []
        
        try:
            logger.info(f"Fetching malware hashes from {url}")
            r = requests.get(url)
            r.raise_for_status()

            # Filter out comment lines
            lines = [
                line
                for line in r.text.splitlines()
                if not line.strip().startswith("#")
            ]

            if not lines:
                return []
                
            # Skip header
            reader = csv.reader(lines[1:])
            
            for row in reader:
                if row and len(row) >= 3:  # Need at least date, sha256, filename
                    # Get SHA256 hash from the row
                    sha256 = row[1].strip()
                    
                    indicator = {
                        "hash": sha256,
                        "type": "hash",
                        "description": f"Malware sample: {row[2] if len(row) > 2 else ''}"
                    }
                    
                    # Add extra data
                    if len(row) > 4:
                        indicator["tags"] = row[4].strip()
                    
                    indicators.append(indicator)
                    
            logger.info(f"Extracted {len(indicators)} hash indicators from MalwareBazaar")
            
        except Exception as e:
            logger.error(f"Error fetching/parsing MalwareBazaar hashes: {e}")
            
        return indicators
