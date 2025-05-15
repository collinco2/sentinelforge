import whois
import geoip2.database
import logging
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

LOG = logging.getLogger(__name__)

# Timeout constant for enrichment operations
ENRICHMENT_TIMEOUT = 10  # seconds


class WhoisGeoIPEnricher:
    def __init__(self, geoip_db_path: str):
        try:
            self.geoip_reader = geoip2.database.Reader(geoip_db_path)
            LOG.info(f"GeoIP database loaded from {geoip_db_path}")
        except Exception as e:
            LOG.error(f"Failed to load GeoIP database from {geoip_db_path}: {e}")
            # Set reader to None but don't raise to avoid crashes
            self.geoip_reader = None

    def _safe_whois_lookup(self, domain: str) -> Dict:
        """Run whois lookup with proper error handling."""
        try:
            w = whois.whois(domain)
            return {
                "registrar": w.registrar,
                "creation_date": w.creation_date,
                "expiration_date": w.expiration_date,
            }
        except Exception as e:
            LOG.warning(f"Whois lookup failed for {domain}: {e}")
            return {}

    def _safe_geoip_lookup(self, ip: str) -> Dict:
        """Run GeoIP lookup with proper error handling."""
        if not self.geoip_reader:
            LOG.warning("GeoIP reader not initialized, skipping lookup")
            return {}

        try:
            geo = self.geoip_reader.city(ip)
            return {
                "country": geo.country.name if geo.country else None,
                "city": geo.city.name if geo.city else None,
                "latitude": geo.location.latitude if geo.location else None,
                "longitude": geo.location.longitude if geo.location else None,
            }
        except Exception as e:
            LOG.warning(f"GeoIP lookup failed for {ip}: {e}")
            return {}

    def _timed_operation(self, func, *args, timeout=ENRICHMENT_TIMEOUT):
        """Execute a function with a timeout to prevent hanging."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                future = executor.submit(func, *args)
                return future.result(timeout=timeout)
            except FutureTimeoutError:
                LOG.warning(f"Operation timed out after {timeout} seconds")
                return {}
            except Exception as e:
                LOG.warning(f"Operation failed: {e}")
                return {}

    def enrich(self, indicator: Dict) -> Optional[Dict]:
        """
        Expect indicator with keys {type: "domain"|"ip", value: str}.
        Returns enrichment dict with registrar, creation_date, country, city, etc.

        Now uses a safer timeout implementation to prevent hanging.
        """
        if not indicator or "type" not in indicator or "value" not in indicator:
            LOG.warning(f"Invalid indicator format: {indicator}")
            return {}

        result = {}
        try:
            ind_type = indicator["type"]
            ind_value = indicator["value"]

            if ind_type == "domain":
                domain_info = self._timed_operation(self._safe_whois_lookup, ind_value)
                result.update(domain_info)
            elif ind_type == "ip":
                geoip_info = self._timed_operation(self._safe_geoip_lookup, ind_value)
                result.update(geoip_info)
            else:
                LOG.warning(f"Unsupported indicator type: {ind_type}")

        except Exception as e:
            LOG.warning(f"Enrichment failed for {indicator}: {e}")

        return result
