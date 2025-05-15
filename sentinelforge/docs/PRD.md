Product Requirement Document (PRD) 

Product Requirements Document (PRD)
AI-Powered Threat Intelligence Aggregator

⸻

1. Overview and Objective

Product Name: AI-Powered Threat Intelligence Aggregator (working title)

Vision: Provide real-time, noise-reduced cyber threat intelligence by aggregating, 
normalizing, and enriching data from multiple public and proprietary feeds, then 
delivering actionable insights to security teams in an intuitive, low-friction 
workflow.

Executives have highlighted a rapid go-to-market opportunity by integrating 10–30 
threat intel feeds into a single consolidated platform, scoring and classifying 
indicators, and providing frictionless exports to SIEM, SOAR, and security 
collaboration channels. Our technical research confirms both the feasibility of this 
aggregation approach and the importance of advanced analytics (AI/ML) to reduce 
noise and prioritize threats effectively.

Primary Objective:

•

Build an MVP that ingests multiple CTI feeds, deduplicates and enriches 

IOCs (Indicators of Compromise), applies rule-based or ML-based scoring, and 
outputs a consolidated, high-value feed for MSSPs, SOC teams, and security 
consultants (vCISOs).

•

Offer a flexible architecture for easy integration and future expansion 
into advanced AI features like LLM-based summarization and automated MITRE 
ATT&CK mapping.

⸻

2. Target Audience & Use Cases

1. MSSPs (Managed Security Service Providers)
•

Provide multi-tenant threat intelligence to protect multiple client 

environments, quickly triaging new or critical IOCs.

•
2.
•

Export or push feed updates into existing SIEM/SOAR workflows.
SOC Analysts (Tier 1–3)
Quickly identify newly reported malicious IPs, domains, or file hashes 

without manual feed-hopping.

•

Leverage the platform's scoring and deduplication to reduce alert 

fatigue.
3.
•
CTI analysts.
•

vCISOs / Fractional CISOs / Smaller Security Teams
Rely on pre-prioritized, noise-reduced intel because they lack dedicated 

Use a simple interface to pivot on IOCs and see relevant enrichment (IP 

reputation, malicious domain info, etc.).

4. Mid-Market Organizations (in finance, healthcare, manufacturing, 

etc.)
•

Need to improve incident response preparedness with current, 

consolidated threat data.

•

Must ensure data compliance (e.g., GDPR) and have lower budgets.

⸻

3. Product Scope

•
•

Scope In:
Aggregation of ~10–30 open-source/public feeds (e.g., AlienVault OTX, 

Abuse.ch, CISA AIS, and more).

•
•

Normalization, deduplication, scoring, and classification of IOCs.
Basic AI-based (rule-based + NLP) threat scoring and optional MITRE 

ATT&CK tagging for TTP-level context.

•

Output integration with standard security tools (SIEM, SOAR) via STIX/

TAXII, JSON, CSV, or webhooks.

Basic user interface for feed management, alert triage, and summary 

Ability to support a quick MVP (2–4 weeks to initial launch).
Scope Out:
Full SOAR functionality (automated playbooks) – we will only provide 

minimal "alert forwarding" at MVP.

•

In-depth analytics for advanced actor attribution or global correlation 

beyond initial AI-based scoring (planned in future phases).

•

Large-scale proprietary threat feed ingestion or data monetization (can 

be considered in expansions).

⸻

4. Key Features & Requirements

4.1 Data Ingestion & Integration

1.
•

Feed Connectors
Integrate with at least 10–30 public threat intelligence sources (e.g., 

CISA AIS, AlienVault OTX, Abuse.ch, PhishTank, etc.).

•

Each connector must handle the source's native format (JSON, STIX/

TAXII, CSV, RSS/XML).

•
dashboards.
•
•
•

multiple feeds.

•
and analysis.
•

•
•

Provide scheduling options (interval or near-real-time fetch).
Reference: Technical research emphasizes using standard libraries 

(e.g., stix2, taxii2-client, or custom CSV/XML parsers) to normalize IOCs.

2. Normalization & Deduplication
•
structure).
•

Convert all raw indicators into a common schema (e.g., STIX 2.1–like 

Deduplicate on indicator_value + type to prevent storing duplicates from 

Track source provenance (e.g., feed name, timestamp) to enable scoring 

Provide an internal caching or hashing mechanism to avoid reprocessing 

identical IOCs.

3. Configurable ETL (Extract-Transform-Load)
•

The pipeline should allow custom logic per feed if needed (e.g., special 

CSV columns, or unique JSON fields).

•

Must accommodate quick additions of new feeds without rewriting core 

ingestion logic.

4.2 Threat Scoring & Enrichment

1.
•

Rule-Based Scoring (MVP)
Combine confidence values from feed sources (if provided) into an 

aggregated score.

•
•

Use heuristics (e.g., "seen in multiple reputable feeds => +X points").
Provide default thresholds (e.g., 0–100 scale, with low/medium/high 

classification) to guide triage.

2. AI/ML-Enhanced Enrichment (Phase 1 Extension)
•

Integrate external reputation services or local ML models to refine 

scoring (domain age, geolocation, WHOIS anomalies).

•
•

Include optional LLM-based summarization of new or trending threats.
Provide MITRE ATT&CK technique tags if a feed or a model identifies 

relevant TTPs (T1566 for phishing, etc.).

•

Reference: Our research notes potential for supervised or semi-

supervised ML that learns from user feedback to improve threat scoring over time.

3.
•

Enrichment APIs
For each IOC, store supplemental data: WHOIS info, historical sightings, 

last-seen date, known threat actors, etc.

•

Allow on-demand queries from external tools (SOAR) or the web UI to 

fetch this context.

4.3 Data Output & Integrations

SIEM & SOAR Integration
Act as a TAXII server so SIEMs (e.g., Splunk, QRadar) can pull curated 

Provide CSV/JSON output endpoints for custom ingestion.

1.
•
STIX feeds.
•

•
2.
•
•

Optionally push to external systems via webhooks or direct API calls.
Slack/Email Notifications
Support basic "alerting" channels for new critical or high-scoring IOCs.
Slack: Use incoming webhook with a short summary plus a link to the 

aggregator's IOC page.

Email: Daily or real-time digests for designated recipients.

•
3. Dashboards & Reporting
• Web-based UI that shows top new threats, feed ingestion status, and 

quick filtering (e.g., only IPs > 80 score).

•

Provide exportable lists (CSV, PDF) of all high-scoring IOCs or weekly 

"top emerging threats."

4.4 User Experience & Access Control

1.
•
•
•
2.
•

Dashboard
Display feed status (last fetch time, # of new IOCs).
Highlight top malicious IOCs and trending threats.
Include basic filtering (e.g., date range, type: IP/domain/hash).
IOC Drill-Down
Let users click on an IOC to see feed provenance, scoring rationale, and 

any correlation (e.g., "This IP has been flagged by X feed with confidence 90").
Show enrichment details (domain WHOIS, geolocation, references to 

•

MITRE ATT&CK if relevant).
3. Multi-User Roles
•

At minimum, provide Admin (manage feeds, settings) and Analyst (view 

and export intel).

•

Future extension: multi-tenant or multi-client environment for MSSPs 

(each client has a segmented view).

4.
•

Performance & UX
The system should ingest new IOCs and reflect them in the UI within a 

typical window of 5–15 minutes, at least in MVP.

•

Searching or filtering for IOCs in the UI should remain responsive (under 

2 seconds) for up to ~1 million stored IOCs.

⸻

5. Architecture & Technical Approach

1. Modular ETL Pipeline
•

Ingestion Service: Periodically fetch raw data from each feed; post to a 

message queue or direct microservice endpoint.

•

Normalization & Dedup Service: Standardize to an internal STIX-like 

schema, remove duplicates, track feed metadata.

•

Enrichment & Scoring Service: Apply AI or heuristic rules; call external 

lookups (VirusTotal, WHOIS, DNS, etc.) if needed.

•

Storage: Store processed IOCs in a scalable, query-friendly database 

(e.g., Elasticsearch or a NoSQL store).

2. API & Output Layer
•
•
•
3. UI Layer
•

Provide a REST/GraphQL API for internal UI and external consumers.
Optionally run an OpenTAXII server for STIX feeds.
Slack/email integration for alerting.

Single-page web app or simple front-end served by the aggregator's 

API.

•
4.
•

Provides search, filtering, feed management, user management.
Scalability Considerations
Use containerization (Docker/Kubernetes) to deploy ingestion, scoring, 

and UI microservices.

•

For MVP, a single region cloud deployment is sufficient; plan for multi-

region or on-prem later.

•

Rate-limiting and retry strategies on feed ingestion to handle feed 

outages or large volume spikes.

5.
•

Security & Compliance
All transit connections (feed ingestion, user access) must use HTTPS/

TLS.

Role-based access control for user logins; integrate with SSO or local 

•
credentials.
•
•
•

Data encryption at rest (cloud KMS or on-prem encryption solutions).
Log all updates (audit logs) with who/what/when for compliance.
Provide data retention policies (e.g., IOC data older than X months can 

be archived).

⸻

6. Deployment Models

1.
•
•
•
governance.

Cloud-Hosted (Default)
Fast time-to-market with minimal customer overhead.
Continuous updates and immediate patching.
Ideal for MSSPs, mid-size organizations, vCISOs with flexible data 

2. On-Premises / Hybrid (Future Option)
•

Some regulated or government entities may require local hosting or air-

gapped solutions.

•

Potential approach: containerized aggregator with local data store, plus 

a "relay" for external feeds in a DMZ.

•

Higher engineering cost; consider offering this after stabilizing the cloud 

version.

⸻

7. Timeline and Roadmap

MVP (2–4 Week Build Cycle)

• Week 1:
•

Stand up ingestion pipeline for at least 5–10 free OSINT feeds (e.g., 

AlienVault OTX, Abuse.ch, CISA AIS).

Implement basic dedup + standard schema.
Barebones UI to display a feed status page and a list of new IOCs.

•
•
• Week 2:
•
•
indicators).
•

Add a basic rule-based scoring engine.
Integrate simple output (CSV export, Slack/webhook for high-scoring 

Begin internal testing with real data, validate feed correctness, and 

confirm minimal false positives or duplicates.

• Week 3–4:
•

Add optional MITRE ATT&CK tagging (simple lookups if feed mentions 

known TTPs).

•
•
•

Implement user roles (admin vs. analyst).
Finalize UI enhancements for filtering, searching IOCs.
Demo to pilot MSSP or friendly SOC for feedback.

Phase 1 Enhancements (Month 2–3)

•
•

Expand feed coverage to 30+ sources.
Add optional LLM-based threat summarization for top campaigns or new 

threat families.

•

Provide STIX/TAXII feed output so SIEMs can pull curated intel 

automatically.

•

Additional AI scoring and correlation (train a model on user feedback or 

large historical datasets).

Phase 2: On-Prem & Advanced AI

•
•

Offer an on-prem or hybrid deployment package.
Expand AI to handle advanced entity resolution (merging multiple alias 

names for same threat actor), deeper automation of MITRE ATT&CK mapping, and 
anomaly detection (new or rare threat patterns).

•

Potentially introduce a "community sharing" feature (like OTX pulses or 

ThreatConnect CAL) where aggregator users can share anonymized intel.

⸻

8. Success Metrics

1.
•

Noise Reduction:
Percentage of aggregated IOCs that are duplicates or low-confidence 

and get filtered out.

•

Target: at least 30–50% duplication or low-value removal vs. raw feed 

volume.

2. Analyst Efficiency:
•

Time saved in triaging new threats compared to manually scanning 

multiple feeds.

•
3.
•

Goal: Reduce triage time by ~50% for pilot MSSPs.
Integration Adoption:
Number of SIEM/SOAR integrations successfully configured within first 

30 days of pilot.

•

Aim: at least 80% of pilot users integrate aggregator data into their 

existing workflows easily.

4. User Feedback & Renewal:
•
•
5.
•

Beta user Net Promoter Score (NPS) or direct satisfaction feedback.
Renewal/continuation rate for early adopters after MVP trial.
Scalability & Performance:
The aggregator should handle up to 1 million IOCs with <2s search 

latency.

•

Ingestion pipeline uptime > 99% monthly.

⸻

9. Risks & Considerations

•

Data Licensing: Some feeds limit redistribution. Ensure EULAs and 

compliance for any feed we bundle in our aggregator.

•

AI Accuracy: Over-reliance on AI can introduce false positives or 

"hallucinated" context. Keep a feedback loop so analysts can correct or downvote 
suspicious classifications.

•

On-Prem Complexity: Supporting local installations could significantly 
increase development and support overhead. Carefully plan for that feature after 
MVP traction.

•

Evolving Threat Landscape: Rapid changes in attacker techniques 

require frequent updates to scoring heuristics and feed connectors. Maintain agile 
release processes.

⸻

10. Conclusion

This Threat Intelligence Aggregator aligns with the executive brainstorm for a 
"noise-reduced, quickly deployable, AI-powered threat feed." By leveraging 
existing open-source feeds, standardized ingestion, and a flexible architecture, we 
can deliver immediate value (MVP in ~4 weeks) to small and mid-sized security 
teams, MSSPs, and vCISOs.

Key differentiators will be:

•
•

Rapid MVP with simple rule-based scoring + deduplication.
AI/ML integration for advanced threat scoring, summarization, and TTP 

tagging.

•

User-friendly, low-code approach for feed ingestion, with minimal 

overhead for new connectors and SIEM integration.

•

Scalability via containerized, cloud-native design or optional on-

premises deployment.

This product requirement document ensures we have a clear path for building, 
validating, and iterating toward a robust Threat Intelligence Aggregator that meets 
both immediate market needs (fast, consolidated threat intel) and future demands 
(advanced AI-driven analysis, compliance, on-prem flexibility).

⸻

End of Document

# Example Environment Variables for SentinelForge
# Rename this file to .env and replace values as needed.

# --- Core ---
# DATABASE_URL=sqlite:///./ioc_store.db # Default
# SCORING_RULES_PATH=scoring_rules.yaml # Default

# --- API ---
# Required for authenticated API endpoints (/export/*)
SENTINELFORGE_API_KEY="super-secret-token" # CHANGE THIS!

# --- Enrichment ---
# Required for GeoIP enrichment (download from MaxMind)
GEOIP_DB_PATH="data/GeoLite2-City.mmdb"

# --- Notifications ---
# Required for Slack alerts
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
SLACK_ALERT_THRESHOLD=80 # Default

# Required for Email digest
SENDGRID_API_KEY="SG.xxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
DIGEST_RECIPIENTS="user1@example.com,user2@example.com"
DIGEST_FROM="sentinelforge@example.com"

