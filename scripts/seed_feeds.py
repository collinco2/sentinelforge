#!/usr/bin/env python3
"""
SentinelForge Demo Feed Seeder

Creates sample threat feeds for testing and demonstration purposes.
Supports multiple formats: STIX 2.0, JSON, CSV, and TXT.

Usage:
    python scripts/seed_feeds.py [--confirm] [--import-data]

Options:
    --confirm      Skip confirmation prompt
    --import-data  Also trigger background import after feed creation

Admin access required.
"""

import sys
import os
import json
import sqlite3
import secrets
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import get_user_by_credentials, UserRole


# Sample feed configurations
DEMO_FEEDS = [
    {
        "name": "MalwareDomainList - Domains",
        "feed_type": "txt",
        "description": "Known malicious domains from MalwareDomainList project",
        "url": "https://www.malwaredomainlist.com/hostslist/hosts.txt",
        "ioc_type": "domain",
        "format_config": {
            "delimiter": "\n",
            "comment_prefix": "#",
            "extract_pattern": r"0\.0\.0\.0\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        },
        "sample_data": [
            "malicious-domain1.com",
            "evil-site.net",
            "phishing-example.org",
            "malware-host.biz",
            "suspicious-domain.info",
        ],
    },
    {
        "name": "Abuse.ch URLhaus - Malware URLs",
        "feed_type": "csv",
        "description": "Malware URLs from Abuse.ch URLhaus database",
        "url": "https://urlhaus.abuse.ch/downloads/csv_recent/",
        "ioc_type": "url",
        "format_config": {
            "has_header": True,
            "delimiter": ",",
            "url_column": "url",
            "threat_column": "threat",
            "tags_column": "tags",
        },
        "sample_data": [
            {
                "url": "http://malicious-payload.xyz/download.php?id=1234",
                "threat": "trojan",
                "tags": "exe,payload",
            },
            {
                "url": "https://evil-site.com/malware.zip",
                "threat": "ransomware",
                "tags": "zip,crypto",
            },
            {
                "url": "http://phishing-bank.net/login.html",
                "threat": "phishing",
                "tags": "banking,credential",
            },
            {
                "url": "https://fake-update.org/flash_update.exe",
                "threat": "trojan",
                "tags": "exe,fake-update",
            },
        ],
    },
    {
        "name": "IPsum Threat Intelligence",
        "feed_type": "txt",
        "description": "Malicious IP addresses from IPsum aggregated feeds",
        "url": "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt",
        "ioc_type": "ip",
        "format_config": {
            "delimiter": "\n",
            "comment_prefix": "#",
            "extract_pattern": r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
        },
        "sample_data": [
            "192.168.100.50",
            "10.0.0.100",
            "203.0.113.45",
            "198.51.100.78",
            "172.16.0.200",
        ],
    },
    {
        "name": "MITRE ATT&CK STIX Feed",
        "feed_type": "json",
        "description": "MITRE ATT&CK techniques and indicators in STIX 2.0 format",
        "url": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
        "ioc_type": "mixed",
        "format_config": {
            "stix_version": "2.0",
            "bundle_key": "objects",
            "indicator_types": ["indicator", "malware", "tool"],
        },
        "sample_data": {
            "type": "bundle",
            "id": "bundle--demo-12345",
            "objects": [
                {
                    "type": "indicator",
                    "id": "indicator--demo-1",
                    "created": "2024-01-01T00:00:00.000Z",
                    "modified": "2024-01-01T00:00:00.000Z",
                    "pattern": "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
                    "labels": ["malicious-activity"],
                },
                {
                    "type": "indicator",
                    "id": "indicator--demo-2",
                    "created": "2024-01-01T00:00:00.000Z",
                    "modified": "2024-01-01T00:00:00.000Z",
                    "pattern": "[domain-name:value = 'evil-command-control.com']",
                    "labels": ["malicious-activity"],
                },
            ],
        },
    },
    {
        "name": "Emerging Threats - Compromised IPs",
        "feed_type": "txt",
        "description": "Compromised IP addresses from Emerging Threats",
        "url": "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt",
        "ioc_type": "ip",
        "format_config": {
            "delimiter": "\n",
            "comment_prefix": "#",
            "extract_pattern": r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
        },
        "sample_data": [
            "185.220.100.240",
            "45.142.214.48",
            "91.219.236.166",
            "194.147.78.112",
            "23.129.64.131",
        ],
    },
]


def get_db_connection():
    """Get database connection."""
    try:
        conn = sqlite3.connect("ioc_store.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def authenticate_admin():
    """Verify admin credentials."""
    print("🔐 Admin authentication required")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    user = get_user_by_credentials(username, password)
    if not user or user.role != UserRole.ADMIN.value:
        print("❌ Admin access required")
        return None

    print(f"✅ Authenticated as {user.username} (Admin)")
    return user


def create_sample_files():
    """Create sample feed files in feeds/ directory."""
    feeds_dir = Path("feeds/demo")
    feeds_dir.mkdir(exist_ok=True)

    print("📁 Creating sample feed files...")

    for feed in DEMO_FEEDS:
        filename = f"demo_{feed['name'].lower().replace(' ', '_').replace('-', '_')}"

        if feed["feed_type"] == "txt":
            filepath = feeds_dir / f"{filename}.txt"
            with open(filepath, "w") as f:
                f.write("# Demo feed data - for testing only\n")
                f.write(f"# Feed: {feed['name']}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                for item in feed["sample_data"]:
                    f.write(f"{item}\n")

        elif feed["feed_type"] == "csv":
            filepath = feeds_dir / f"{filename}.csv"
            with open(filepath, "w") as f:
                if feed["sample_data"]:
                    # Write header
                    headers = list(feed["sample_data"][0].keys())
                    f.write(",".join(headers) + "\n")
                    # Write data
                    for item in feed["sample_data"]:
                        values = [str(item.get(h, "")) for h in headers]
                        f.write(",".join(values) + "\n")

        elif feed["feed_type"] == "json":
            filepath = feeds_dir / f"{filename}.json"
            with open(filepath, "w") as f:
                json.dump(feed["sample_data"], f, indent=2)

        print(f"  ✅ Created {filepath}")

    return feeds_dir


def register_feeds(admin_user):
    """Register demo feeds in the database."""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("📋 Registering demo feeds...")

    try:
        for feed in DEMO_FEEDS:
            # Check if feed already exists
            cursor.execute(
                "SELECT id FROM threat_feeds WHERE name = ?", (feed["name"],)
            )
            if cursor.fetchone():
                print(f"  ⏭️  Skipped existing: {feed['name']}")
                continue

            # Insert feed record (let database auto-generate ID)
            cursor.execute(
                """
                INSERT INTO threat_feeds
                (name, feed_type, description, url, format_config,
                 is_active, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    feed["name"],
                    feed["feed_type"],
                    feed["description"],
                    feed["url"],
                    json.dumps(feed["format_config"]),
                    1,  # is_active
                    admin_user.user_id,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            print(f"  ✅ Registered: {feed['name']}")

        conn.commit()
        print(f"🎉 Successfully registered {len(DEMO_FEEDS)} demo feeds")
        return True

    except Exception as e:
        print(f"❌ Error registering feeds: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def import_sample_data(admin_user):
    """Import sample IOC data for each feed."""
    from services.ingestion import process_feed_data

    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    print("📥 Importing sample IOC data...")

    try:
        # Get registered demo feeds
        cursor.execute("""
            SELECT id, name, feed_type FROM threat_feeds 
            WHERE name LIKE '%MalwareDomainList%' 
               OR name LIKE '%Abuse.ch%'
               OR name LIKE '%IPsum%'
               OR name LIKE '%MITRE%'
               OR name LIKE '%Emerging%'
        """)

        feeds = cursor.fetchall()

        for feed in feeds:
            feed_id = feed["id"]
            feed_name = feed["name"]

            # Find corresponding demo data
            demo_feed = next((f for f in DEMO_FEEDS if f["name"] == feed_name), None)
            if not demo_feed:
                continue

            print(f"  📊 Processing {feed_name}...")

            # Create import log entry
            cursor.execute(
                """
                INSERT INTO feed_import_logs
                (feed_id, feed_name, import_type, import_status, user_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    feed_id,
                    feed_name,
                    "demo_setup",
                    "processing",
                    admin_user.user_id,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            import_log_id = cursor.lastrowid

            # Process sample data based on type
            iocs_imported = 0

            if demo_feed["feed_type"] in ["txt"]:
                for ioc_value in demo_feed["sample_data"]:
                    # Insert IOC
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO iocs 
                        (ioc_type, ioc_value, source_feed, severity, confidence, 
                         first_seen, last_seen, is_active, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            demo_feed["ioc_type"],
                            ioc_value,
                            feed_name,
                            "medium",
                            85,
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                            1,
                            admin_user.user_id,
                        ),
                    )
                    if cursor.rowcount > 0:
                        iocs_imported += 1

            elif demo_feed["feed_type"] == "csv":
                for item in demo_feed["sample_data"]:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO iocs 
                        (ioc_type, ioc_value, source_feed, severity, confidence,
                         tags, first_seen, last_seen, is_active, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            demo_feed["ioc_type"],
                            item["url"],
                            feed_name,
                            "high",
                            90,
                            item.get("tags", ""),
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                            1,
                            admin_user.user_id,
                        ),
                    )
                    if cursor.rowcount > 0:
                        iocs_imported += 1

            elif demo_feed["feed_type"] == "json":
                # Process STIX bundle
                if "objects" in demo_feed["sample_data"]:
                    for obj in demo_feed["sample_data"]["objects"]:
                        if obj.get("type") == "indicator":
                            # Extract IOC from STIX pattern
                            pattern = obj.get("pattern", "")
                            if "domain-name:value" in pattern:
                                ioc_value = (
                                    pattern.split("'")[1] if "'" in pattern else ""
                                )
                                ioc_type = "domain"
                            elif "file:hashes.MD5" in pattern:
                                ioc_value = (
                                    pattern.split("'")[1] if "'" in pattern else ""
                                )
                                ioc_type = "hash"
                            else:
                                continue

                            if ioc_value:
                                cursor.execute(
                                    """
                                    INSERT OR IGNORE INTO iocs 
                                    (ioc_type, ioc_value, source_feed, severity, confidence,
                                     first_seen, last_seen, is_active, created_by)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                    (
                                        ioc_type,
                                        ioc_value,
                                        feed_name,
                                        "high",
                                        95,
                                        datetime.now(timezone.utc).isoformat(),
                                        datetime.now(timezone.utc).isoformat(),
                                        1,
                                        admin_user.user_id,
                                    ),
                                )
                                if cursor.rowcount > 0:
                                    iocs_imported += 1

            # Update import log
            cursor.execute(
                """
                UPDATE feed_import_logs
                SET import_status = ?, imported_count = ?,
                    total_records = ?, timestamp = ?
                WHERE id = ?
            """,
                (
                    "completed",
                    iocs_imported,
                    len(demo_feed["sample_data"])
                    if isinstance(demo_feed["sample_data"], list)
                    else 2,
                    datetime.now(timezone.utc).isoformat(),
                    import_log_id,
                ),
            )

            print(f"    ✅ Imported {iocs_imported} IOCs")

        conn.commit()
        print("🎉 Sample data import completed successfully")
        return True

    except Exception as e:
        print(f"❌ Error importing sample data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main execution function."""
    print("🚀 SentinelForge Demo Feed Seeder")
    print("=" * 50)

    # Parse arguments
    import argparse

    parser = argparse.ArgumentParser(description="Seed demo threat feeds")
    parser.add_argument(
        "--confirm", action="store_true", help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--import-data", action="store_true", help="Also import sample IOC data"
    )
    args = parser.parse_args()

    # Confirmation
    if not args.confirm:
        print("\n⚠️  This will create demo threat feeds and sample data.")
        print("   Existing feeds with the same names will be skipped.")
        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != "y":
            print("❌ Cancelled")
            return

    # Authenticate admin
    admin_user = authenticate_admin()
    if not admin_user:
        return

    # Create sample files
    feeds_dir = create_sample_files()

    # Register feeds
    if not register_feeds(admin_user):
        return

    # Import sample data if requested
    if args.import_data:
        if not import_sample_data(admin_user):
            return

    print("\n🎉 Demo feed setup completed successfully!")
    print(f"📁 Sample files created in: {feeds_dir}")
    print("🌐 Access feeds via: http://localhost:3000/feeds")

    if args.import_data:
        print("📊 Sample IOC data has been imported")
        print("🔍 View IOCs at: http://localhost:3000/iocs")


if __name__ == "__main__":
    main()
