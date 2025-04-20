import whois
import geoip2.database
import logging
from typing import Dict

LOG = logging.getLogger(__name__)


class WhoisGeoIPEnricher:
    def __init__(self, geoip_db_path: str):
        self.geoip_reader = geoip2.database.Reader(geoip_db_path)

    def enrich(self, indicator: Dict) -> Dict:
        """
        Expect indicator with keys {type: "domain"|"ip", value: str}.
        Returns enrichment dict with registrar, creation_date, country, city, etc.
        """
        result = {}
        try:
            if indicator["type"] == "domain":
                w = whois.whois(indicator["value"])
                result.update(
                    {
                        "registrar": w.registrar,
                        "creation_date": w.creation_date,
                        "expiration_date": w.expiration_date,
                    }
                )
            elif indicator["type"] == "ip":
                geo = self.geoip_reader.city(indicator["value"])
                result.update(
                    {
                        "country": geo.country.name,
                        "city": geo.city.name,
                        "latitude": geo.location.latitude,
                        "longitude": geo.location.longitude,
                    }
                )
        except Exception as e:
            LOG.warning("Enrichment failed for %s: %s", indicator, e)
        return result
