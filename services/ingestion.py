#!/usr/bin/env python3
"""
🔄 SentinelForge Threat Feed Ingestion Service

This module provides comprehensive threat feed ingestion capabilities including:
- Multi-format parsing (CSV, JSON, TXT, STIX)
- IOC normalization and validation
- Duplicate detection and handling
- Bulk import optimization
- Audit logging and error tracking

Usage:
    from services.ingestion import FeedIngestionService

    service = FeedIngestionService()
    result = service.import_from_file(file_path, source_feed="My Feed")
"""

import csv
import json
import re
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from io import StringIO, TextIOWrapper
import sqlite3
from pathlib import Path


class IOCValidator:
    """Validates and normalizes IOC data."""

    @staticmethod
    def infer_ioc_type(value: str) -> str:
        """Infer IOC type from value pattern."""
        if not isinstance(value, str) or not value.strip():
            return "unknown"

        value = value.strip()

        # URL pattern (check first as it's most specific)
        if re.match(r"^https?://", value, re.IGNORECASE):
            return "url"

        # IP address pattern (check before domain to avoid false positives)
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value):
            # Validate IP ranges
            try:
                parts = value.split(".")
                if all(0 <= int(part) <= 255 for part in parts):
                    return "ip"
            except ValueError:
                pass

        # Hash patterns (MD5, SHA1, SHA256, SHA512)
        if re.match(r"^[a-fA-F0-9]{32}$", value):  # MD5
            return "hash"
        elif re.match(r"^[a-fA-F0-9]{40}$", value):  # SHA1
            return "hash"
        elif re.match(r"^[a-fA-F0-9]{64}$", value):  # SHA256
            return "hash"
        elif re.match(r"^[a-fA-F0-9]{128}$", value):  # SHA512
            return "hash"

        # Email pattern (check before domain as it's more specific)
        elif re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            return "email"

        # Domain pattern (check last as it's most general)
        elif re.match(
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$",
            value,
        ):
            return "domain"

        return "unknown"

    @staticmethod
    def validate_ioc(ioc_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate IOC data and return (is_valid, errors)."""
        errors = []

        # Required fields
        if not ioc_data.get("ioc_value", "").strip():
            errors.append("IOC value is required")

        if not ioc_data.get("ioc_type", "").strip():
            errors.append("IOC type is required")

        # Validate IOC type
        valid_types = ["ip", "domain", "url", "hash", "email"]
        ioc_type = ioc_data.get("ioc_type", "").lower()
        if ioc_type not in valid_types:
            errors.append(
                f"Invalid IOC type: {ioc_type}. Must be one of: {', '.join(valid_types)}"
            )

        # Validate score range
        score = ioc_data.get("score")
        if score is not None:
            try:
                score_float = float(score)
                if not (0 <= score_float <= 10):
                    errors.append("Score must be between 0 and 10")
            except (ValueError, TypeError):
                errors.append("Score must be a valid number")

        # Validate confidence range
        confidence = ioc_data.get("confidence")
        if confidence is not None:
            try:
                confidence_int = int(confidence)
                if not (0 <= confidence_int <= 100):
                    errors.append("Confidence must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append("Confidence must be a valid integer")

        return len(errors) == 0, errors

    @staticmethod
    def normalize_ioc(ioc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize IOC data to standard format."""
        normalized = {}

        # Handle field mapping variations
        value_fields = ["ioc_value", "value", "indicator", "ioc"]
        type_fields = ["ioc_type", "type", "indicator_type"]

        # Extract IOC value
        for field in value_fields:
            if field in ioc_data and ioc_data[field]:
                normalized["ioc_value"] = str(ioc_data[field]).strip()
                break

        # Extract IOC type
        for field in type_fields:
            if field in ioc_data and ioc_data[field]:
                normalized["ioc_type"] = str(ioc_data[field]).lower().strip()
                break

        # Auto-detect type if not provided
        if "ioc_type" not in normalized and "ioc_value" in normalized:
            normalized["ioc_type"] = IOCValidator.infer_ioc_type(
                normalized["ioc_value"]
            )

        # Standard fields with defaults
        normalized["source_feed"] = str(ioc_data.get("source_feed", "Unknown")).strip()
        normalized["severity"] = str(ioc_data.get("severity", "medium")).lower().strip()
        normalized["confidence"] = int(ioc_data.get("confidence", 50))

        # Score handling
        score = ioc_data.get("score", 5.0)
        try:
            normalized["score"] = float(score)
        except (ValueError, TypeError):
            normalized["score"] = 5.0

        # Tags handling
        tags = ioc_data.get("tags", [])
        if isinstance(tags, str):
            # Split comma-separated tags
            normalized["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
        elif isinstance(tags, list):
            normalized["tags"] = [str(tag).strip() for tag in tags if str(tag).strip()]
        else:
            normalized["tags"] = []

        # Timestamps
        normalized["first_seen"] = datetime.utcnow()
        normalized["last_seen"] = datetime.utcnow()
        normalized["created_at"] = datetime.utcnow()
        normalized["updated_at"] = datetime.utcnow()
        normalized["is_active"] = True

        return normalized


class FeedParser:
    """Parses different feed formats."""

    @staticmethod
    def parse_csv(file_content: str) -> List[Dict[str, Any]]:
        """Parse CSV format feed."""
        iocs = []
        lines = file_content.strip().split("\n")

        # Skip comment lines at the beginning (for Abuse.ch format)
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("#") or not line.strip():
                data_start = i + 1
            else:
                break

        # Get the actual CSV data
        csv_data = "\n".join(lines[data_start:])
        if not csv_data.strip():
            return iocs

        try:
            reader = csv.DictReader(StringIO(csv_data))

            for row_num, row in enumerate(
                reader, start=data_start + 2
            ):  # Account for skipped lines
                if not any(row.values()):  # Skip empty rows
                    continue

                # Handle Abuse.ch URLhaus format specifically
                if "url" in row and "url_status" in row:
                    # Map Abuse.ch fields to standard IOC format
                    ioc = {
                        "ioc_value": row.get("url", "").strip('"'),
                        "ioc_type": "url",
                        "severity": "high"
                        if row.get("threat") == "malware_download"
                        else "medium",
                        "confidence": 85,  # High confidence for URLhaus
                        "tags": [
                            tag.strip()
                            for tag in row.get("tags", "").split(",")
                            if tag.strip()
                        ],
                        "_row_number": row_num,
                        "_original_row": row,
                    }
                    iocs.append(ioc)
                else:
                    # Standard CSV format
                    row["_row_number"] = row_num
                    iocs.append(row)

        except Exception as e:
            # Fallback to simple CSV parsing
            reader = csv.DictReader(StringIO(file_content))
            for row_num, row in enumerate(reader, start=2):
                if not any(row.values()):
                    continue
                row["_row_number"] = row_num
                iocs.append(row)

        return iocs

    @staticmethod
    def parse_json(file_content: str) -> List[Dict[str, Any]]:
        """Parse JSON format feed."""
        try:
            data = json.loads(file_content)

            # Handle different JSON structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Look for common array keys
                for key in ["iocs", "indicators", "data", "items"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # If no array found, treat as single IOC
                return [data]
            else:
                raise ValueError("Invalid JSON structure")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    @staticmethod
    def parse_txt(file_content: str) -> List[Dict[str, Any]]:
        """Parse plain text format (one IOC per line)."""
        iocs = []
        lines = file_content.strip().split("\n")

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check if this is AlienVault OTX format (IP#score#confidence#description#country...)
            if "#" in line and line.count("#") >= 3:
                parts = line.split("#")
                if len(parts) >= 4:
                    ip_address = parts[0].strip()
                    score = parts[1].strip()
                    confidence = parts[2].strip()
                    description = parts[3].strip()

                    # Validate IP address format
                    ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
                    if re.match(ip_pattern, ip_address):
                        ioc = {
                            "ioc_value": ip_address,
                            "ioc_type": "ip",
                            "severity": "medium" if score == "4" else "low",
                            "confidence": min(int(confidence) * 10, 100)
                            if confidence.isdigit()
                            else 50,
                            "tags": [description] if description else [],
                            "_row_number": line_num,
                        }
                        iocs.append(ioc)
                        continue

            # Standard TXT format - one IOC per line
            ioc = {"ioc_value": line, "_row_number": line_num}
            iocs.append(ioc)

        return iocs

    @staticmethod
    def parse_stix(file_content: str) -> List[Dict[str, Any]]:
        """Parse simple STIX format (basic implementation)."""
        # This is a simplified STIX parser for basic indicator objects
        try:
            data = json.loads(file_content)
            iocs = []

            # Look for STIX objects
            objects = data.get("objects", [])
            for obj in objects:
                if obj.get("type") == "indicator":
                    pattern = obj.get("pattern", "")

                    # Extract IOC from pattern (simplified)
                    # Example: "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']"
                    if "=" in pattern:
                        value = pattern.split("=")[-1].strip().strip("'\"[]")
                        ioc_type = "unknown"

                        # Determine type from pattern
                        if "file:hashes" in pattern:
                            ioc_type = "hash"
                        elif "domain-name:value" in pattern:
                            ioc_type = "domain"
                        elif "ipv4-addr:value" in pattern:
                            ioc_type = "ip"
                        elif "url:value" in pattern:
                            ioc_type = "url"

                        ioc = {
                            "ioc_value": value,
                            "ioc_type": ioc_type,
                            "confidence": obj.get("confidence", 50),
                            "labels": obj.get("labels", []),
                        }
                        iocs.append(ioc)

            return iocs

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid STIX JSON format: {e}")


class FeedIngestionService:
    """Main service for threat feed ingestion."""

    def __init__(self, db_path: str = "/Users/Collins/sentinelforge/ioc_store.db"):
        self.db_path = db_path
        self.validator = IOCValidator()
        self.parser = FeedParser()

    def get_db_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def detect_file_format(self, filename: str, content: str) -> str:
        """Detect file format from filename and content."""
        filename_lower = filename.lower()

        if filename_lower.endswith(".csv"):
            return "csv"
        elif filename_lower.endswith(".json"):
            return "json"
        elif filename_lower.endswith(".txt"):
            return "txt"
        elif filename_lower.endswith(".stix") or "stix" in filename_lower:
            return "stix"

        # Try to detect from content
        content_sample = content.strip()[:1000]

        if content_sample.startswith("{") or content_sample.startswith("["):
            return "json"
        elif "," in content_sample and "\n" in content_sample:
            return "csv"
        else:
            return "txt"

    def check_duplicate(self, conn, ioc_type: str, ioc_value: str) -> bool:
        """Check if IOC already exists in database."""
        cursor = conn.execute(
            "SELECT COUNT(*) FROM iocs WHERE ioc_type = ? AND ioc_value = ?",
            (ioc_type, ioc_value),
        )
        count = cursor.fetchone()[0]
        return count > 0

    def insert_ioc(self, conn, ioc_data: Dict[str, Any]) -> bool:
        """Insert IOC into database."""
        try:
            # Convert tags list to JSON string
            tags_json = json.dumps(ioc_data.get("tags", []))

            # Convert enrichment_data to JSON string if it's not already
            enrichment_data = ioc_data.get("enrichment_data", {})
            if isinstance(enrichment_data, dict):
                enrichment_data = json.dumps(enrichment_data)

            conn.execute(
                """
                INSERT INTO iocs (
                    ioc_type, ioc_value, source_feed, first_seen, last_seen,
                    score, category, enrichment_data, severity, tags, confidence,
                    created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ioc_data["ioc_type"],
                    ioc_data["ioc_value"],
                    ioc_data["source_feed"],
                    ioc_data["first_seen"],
                    ioc_data["last_seen"],
                    int(ioc_data["score"]),
                    ioc_data["severity"],  # category
                    enrichment_data,
                    ioc_data["severity"],
                    tags_json,
                    ioc_data["confidence"],
                    ioc_data["created_at"],
                    ioc_data["updated_at"],
                    ioc_data["is_active"],
                ),
            )
            return True
        except Exception as e:
            print(f"Error inserting IOC: {e}")
            print(f"IOC data: {ioc_data}")
            return False

    def log_import(self, conn, log_data: Dict[str, Any]) -> int:
        """Log import operation and return log ID."""
        cursor = conn.execute(
            """
            INSERT INTO feed_import_logs (
                feed_id, feed_name, import_type, file_name, file_size,
                total_records, imported_count, skipped_count, error_count,
                errors, import_status, duration_seconds, user_id,
                justification, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                log_data.get("feed_id"),
                log_data["feed_name"],
                log_data["import_type"],
                log_data.get("file_name"),
                log_data.get("file_size"),
                log_data["total_records"],
                log_data["imported_count"],
                log_data["skipped_count"],
                log_data["error_count"],
                json.dumps(log_data.get("errors", [])),
                log_data["import_status"],
                log_data.get("duration_seconds"),
                log_data["user_id"],
                log_data.get("justification"),
                datetime.utcnow(),
            ),
        )
        return cursor.lastrowid

    def import_from_file(
        self,
        file_path: str,
        source_feed: str,
        user_id: int,
        justification: str = None,
        feed_id: int = None,
    ) -> Dict[str, Any]:
        """Import IOCs from a file."""
        start_time = time.time()

        # Read file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {e}",
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "errors": [],
            }

        return self.import_from_content(
            content=content,
            filename=Path(file_path).name,
            source_feed=source_feed,
            user_id=user_id,
            justification=justification,
            feed_id=feed_id,
        )

    def import_from_content(
        self,
        content: str,
        filename: str,
        source_feed: str,
        user_id: int,
        justification: str = None,
        feed_id: int = None,
    ) -> Dict[str, Any]:
        """Import IOCs from file content."""
        start_time = time.time()

        # Detect format
        file_format = self.detect_file_format(filename, content)

        # Parse content
        try:
            if file_format == "csv":
                raw_iocs = self.parser.parse_csv(content)
            elif file_format == "json":
                raw_iocs = self.parser.parse_json(content)
            elif file_format == "txt":
                raw_iocs = self.parser.parse_txt(content)
            elif file_format == "stix":
                raw_iocs = self.parser.parse_stix(content)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_format}",
                    "imported_count": 0,
                    "skipped_count": 0,
                    "error_count": 0,
                    "errors": [],
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse {file_format} content: {e}",
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "errors": [],
            }

        # Process IOCs
        return self._process_iocs(
            raw_iocs=raw_iocs,
            source_feed=source_feed,
            user_id=user_id,
            justification=justification,
            feed_id=feed_id,
            filename=filename,
            file_size=len(content.encode("utf-8")),
            start_time=start_time,
        )

    def _process_iocs(
        self,
        raw_iocs: List[Dict[str, Any]],
        source_feed: str,
        user_id: int,
        justification: str,
        feed_id: int,
        filename: str,
        file_size: int,
        start_time: float,
    ) -> Dict[str, Any]:
        """Process and import IOCs into database."""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        conn = self.get_db_connection()

        try:
            conn.execute("BEGIN TRANSACTION")

            for i, raw_ioc in enumerate(raw_iocs):
                try:
                    # Set source feed
                    raw_ioc["source_feed"] = source_feed

                    # Normalize IOC
                    normalized_ioc = self.validator.normalize_ioc(raw_ioc)

                    # Validate IOC
                    is_valid, validation_errors = self.validator.validate_ioc(
                        normalized_ioc
                    )

                    if not is_valid:
                        error_count += 1
                        row_ref = f"Row {raw_ioc.get('_row_number', i + 1)}"
                        errors.append(f"{row_ref}: {'; '.join(validation_errors)}")
                        continue

                    # Check for duplicates
                    if self.check_duplicate(
                        conn, normalized_ioc["ioc_type"], normalized_ioc["ioc_value"]
                    ):
                        skipped_count += 1
                        continue

                    # Insert IOC
                    if self.insert_ioc(conn, normalized_ioc):
                        imported_count += 1
                    else:
                        error_count += 1
                        row_ref = f"Row {raw_ioc.get('_row_number', i + 1)}"
                        errors.append(f"{row_ref}: Failed to insert IOC")

                except Exception as e:
                    error_count += 1
                    row_ref = f"Row {raw_ioc.get('_row_number', i + 1)}"
                    errors.append(f"{row_ref}: {str(e)}")

            # Determine import status
            total_processed = imported_count + skipped_count + error_count
            if error_count == 0:
                import_status = "success"
            elif imported_count > 0:
                import_status = "partial"
            else:
                import_status = "failed"

            # Log import
            duration = int(time.time() - start_time)
            log_data = {
                "feed_id": feed_id,
                "feed_name": source_feed,
                "import_type": "manual" if feed_id is None else "automatic",
                "file_name": filename,
                "file_size": file_size,
                "total_records": len(raw_iocs),
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "errors": errors,
                "import_status": import_status,
                "duration_seconds": duration,
                "user_id": user_id,
                "justification": justification,
            }

            log_id = self.log_import(conn, log_data)

            conn.execute("COMMIT")

            return {
                "success": import_status in ["success", "partial"],
                "import_status": import_status,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "errors": errors[:50],  # Limit errors in response
                "total_records": len(raw_iocs),
                "duration_seconds": duration,
                "log_id": log_id,
            }

        except Exception as e:
            conn.execute("ROLLBACK")
            return {
                "success": False,
                "error": f"Database error: {e}",
                "imported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "errors": [],
            }

        finally:
            conn.close()
