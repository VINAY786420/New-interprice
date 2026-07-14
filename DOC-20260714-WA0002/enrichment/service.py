"""Data enrichment service - emails, phone numbers, company info."""
import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from app.core.logging import logger
from app.core.config import settings


@dataclass
class EnrichedContact:
    """Enriched contact information."""
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    confidence_score: float = 0.0
    sources: List[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []


class DataEnrichmentService:
    """Service for enriching scraped data with contact information."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

    # ==================== EMAIL EXTRACTION ====================

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return list(set(emails))  # Remove duplicates

    def find_email_from_username(self, username: str, platform: str) -> Optional[str]:
        """Try to find email from social media username."""
        # Common patterns
        patterns = [
            f"{username}@gmail.com",
            f"{username}@yahoo.com",
            f"{username}@outlook.com",
            f"{username}@hotmail.com",
        ]

        # Try to verify via Hunter.io or similar (if API key available)
        if hasattr(settings, 'HUNTER_API_KEY') and settings.HUNTER_API_KEY:
            return self._hunter_lookup(username)

        return None

    def _hunter_lookup(self, domain: str) -> Optional[str]:
        """Lookup email via Hunter.io API."""
        try:
            url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={settings.HUNTER_API_KEY}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                emails = data.get("data", {}).get("emails", [])
                if emails:
                    return emails[0].get("value")
        except Exception as e:
            logger.error(f"Hunter lookup failed: {e}")
        return None

    def guess_company_email(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """Generate likely company email patterns."""
        f = first_name.lower()
        l = last_name.lower()
        fi = f[0] if f else ""
        li = l[0] if l else ""

        patterns = [
            f"{f}@{domain}",
            f"{f}.{l}@{domain}",
            f"{f}{l}@{domain}",
            f"{fi}{l}@{domain}",
            f"{f}{li}@{domain}",
            f"{f}_{l}@{domain}",
            f"{l}@{domain}",
            f"{l}.{f}@{domain}",
        ]

        return list(set(patterns))

    # ==================== PHONE EXTRACTION ====================

    def extract_phones(self, text: str, country_code: str = "IN") -> List[str]:
        """Extract phone numbers from text."""
        phones = []

        # Indian format
        if country_code == "IN":
            # +91 XXXXX XXXXX or 0XXXXXXXXXX or XXXXXXXXXX
            patterns = [
                r'\+91[-\s]?[6-9]\d{9}',
                r'\b0[6-9]\d{9}\b',
                r'\b[6-9]\d{9}\b',
            ]
        else:
            # Generic international
            patterns = [
                r'\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}',
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)

        return list(set(phones))

    def format_indian_phone(self, phone: str) -> str:
        """Format Indian phone number consistently."""
        digits = re.sub(r'\D', '', phone)

        if len(digits) == 10:
            return f"+91 {digits}"
        elif len(digits) == 11 and digits.startswith("0"):
            return f"+91 {digits[1:]}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"

        return phone

    # ==================== COMPANY INFO ====================

    def extract_company_info(self, text: str, bio: str = "") -> Dict[str, Any]:
        """Extract company information from text."""
        combined = f"{text} {bio}"

        info = {
            "company_name": None,
            "job_title": None,
            "industry": None,
            "company_size": None,
            "location": None,
            "website": None,
        }

        # Extract company mentions
        company_patterns = [
            r'(?:at|@|with|working at|employed at|\bfor\b)\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\.|,|\||\n|$)',
            r'\b([A-Z][A-Za-z0-9\s&.,]{2,50})\s+(?:Inc\.|LLC|Ltd\.|Limited|Corp\.|Corporation|GmbH|Pvt\. Ltd\.)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                info["company_name"] = match.group(1).strip()
                break

        # Extract job title
        title_patterns = [
            r'\b(CEO|CTO|CFO|COO|CMO|Founder|Co-Founder|Director|Manager|Engineer|Developer|Designer|Consultant|Analyst|Specialist|Head of|VP|Vice President)\b',
            r'\b(Senior|Junior|Lead|Principal|Staff)\s+(\w+)\b',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                info["job_title"] = match.group(0)
                break

        # Extract website
        website_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
        match = re.search(website_pattern, combined)
        if match:
            info["website"] = match.group(0)

        # Extract location
        location_patterns = [
            r'\b(Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Kolkata|Pune|Ahmedabad|Jaipur|Lucknow|Kanpur|Nagpur|Indore|Thane|Bhopal|Visakhapatnam|Patna|Vadodara|Ghaziabad|Ludhiana|Agra|Nashik|Faridabad|Meerut|Rajkot|Kalyan|Vasai|Varanasi|Srinagar|Aurangabad|Dhanbad|Amritsar|Navi Mumbai|Allahabad|Ranchi|Howrah|Coimbatore|Jabalpur|Gwalior|Vijayawada|Jodhpur|Madurai|Raipur|Kota|Guwahati|Chandigarh|Solapur|Hubli|Tiruchirappalli|Mysore|Bareilly|Aligarh|Tiruppur|Gurgaon)\b',
            r'\b(New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|Austin|Jacksonville|Fort Worth|Columbus|Charlotte|San Francisco|Indianapolis|Seattle|Denver|Washington|Boston|El Paso|Detroit|Nashville|Oklahoma City|Portland|Las Vegas|Louisville|Baltimore|Milwaukee|Albuquerque|Tucson|Fresno|Sacramento|Mesa|Kansas City|Atlanta|Long Beach|Colorado Springs|Raleigh|Miami|Virginia Beach|Omaha|Oakland|Minneapolis|Tulsa|Arlington|New Orleans|Wichita|Cleveland|Tampa|Bakersfield|Aurora|Anaheim|Honolulu|Santa Ana|Riverside|Corpus Christi|Lexington|Stockton|Henderson|Saint Paul|St\. Louis|Cincinnati|Pittsburgh|Greensboro|Lincoln|Anchorage|Plano|Orlando|Irvine|Newark|Durham|Chula Vista|Toledo|Fort Wayne|St\. Petersburg|Laredo|Jersey City|Chandler|Madison|Lubbock|Scottsdale|Reno|Buffalo|Gilbert|Glendale|North Las Vegas|Winston\x96Salem|Chesapeake|Norfolk|Fremont|Garland|Irving|Hialeah|Richmond|Boise|Spokane|Baton Rouge|Des Moines|Tacoma|San Bernardino|Modesto|Fontana|Santa Clarita|Birmingham|Oxnard|Fayetteville|Moreno Valley|Rochester|Glendale|Huntington Beach|Salt Lake City|Grand Rapids|Amarillo|Yonkers|Aurora|Montgomery|Akron|Little Rock|Huntsville|Augusta|Grand Prairie|Shreveport|Overland Park|Cleveland|Cape Coral|Knoxville|Oceanside|Sioux Falls|Vancouver|Providence|Fort Lauderdale|Chattanooga|Tempe|Brownsville|Garden Grove|Rancho Cucamonga|Santa Rosa|Peoria|Pomona|Springfield|Corona|Jackson|Pembroke Pines|Hollywood|Salinas|Hayward|Palmdale|Lancaster|Alexandria|Sunnyvale|Springfield|Macon|Kansas City|Paterson|Lakewood|Hollywood|Killeen|Syracuse|Escondido|Pasadena|Bellevue|Mesquite|Charleston|Savannah|Orange|Fullerton|Thornton|McAllen|Round Rock|Waco|Sterling Heights|Denton|Midland|New Haven|Miramar|West Valley City|Olathe|Carrollton|Coral Springs|Stamford|Simi Valley|Concord|Topeka|Westminster|Allentown|Victorville|Abilene|Norman|Beaumont|Independence|Murfreesboro|Ann Arbor|Berkeley|Provo|El Monte|Columbia|Clarksville|Springfield|Lansing|Fargo|Downey|Costa Mesa|Wilmington|Arvada|Inglewood|Miami Gardens|Carlsbad|Westminster|Rochester|Gresham|Clearwater|Lowell|Manchester|West Jordan|Billings|Wichita Falls|Green Bay|Daly City|Burbank|Richardson|Pompano Beach|North Charleston|Broken Arrow|Boulder|West Palm Beach|Santa Maria|El Cajon|Davenport|Rialto|Las Cruces|San Mateo|Lewisville|South Bend|Lakeland|Tyler|Pearland|College Station|League City|Allen|Ventura|Nampa|Edinburg|Vacaville|Sparks|Greeley|Brockton|Everett|Davie|South Gate|Roswell|Waukegan|Dearborn|Centennial|Jurupa Valley|Portsmouth|Chico|Duluth|Sioux City|Bellingham|New Bedford|Cedar Rapids|Clinton|Trenton|Hemet|Bloomington|Mission Viejo|Meridian|Compton|Fishers|Menifee|Lawton|Quincy|Champaign|Danbury|Orem|Buena Park|Hillsboro|Wheaton|Hawthorne|Tustin|Alameda|Kalamazoo|Baytown|Upland|Bethlehem|Pflugerville|Lafayette|Frederick|Lake Charles|San Angelo|Cicero|Missouri City|Chino|Fall River|Carson|St\. Joseph|Goodyear|Plantation|Lawrence|Kenosha|Asheville|Decatur|Plymouth|Deltona|Redwood City|Mount Pleasant|San Marcos|Bowling Green|Palm Coast|Avondale|Gaithersburg|Appleton|Lorain|Lauderhill|Newport Beach|Mount Vernon|San Leandro|Passaic|Rock Hill|Jacksonville|Franklin|St\. Clair Shores|Carmel|Whittier|Cedar Park|Fishers|Dublin|Westland|Bloomington|O\'Fallon|Haverhill|Auburn|Conroe|Wilmington|Jackson|Warner Robins|Arlington Heights|Union City|Johns Creek|Rapid City|Gulfport|Bismarck|Framingham|Blaine|Alpharetta|Schaumburg|Brentwood|Hamilton|Deerfield Beach|Albany|Bowie|Southfield|Dothan|Anderson|Rochester Hills|Newton|Dale City|Springdale|Missoula|Joplin|Pine Bluff|Kannapolis|Waukesha|North Richland Hills|Greenville|Middletown|Noblesville|Kettering|Calumet City|Harrisonburg|La Crosse|Huntersville|New Brunswick|Apopka|Maricopa|Lodi|Maple Grove|Eden Prairie|Coon Rapids|Avon|Gaithersburg|Chelsea|Weslaco|Caldwell|Brunswick|Doral|Cerritos|Cumberland|Danville|Manhattan|Lincoln Park|East Orange|Grapevine|Wylie|White Plains|Elmhurst|Lakewood|Royal Oak|Portland|St\. Peters|Woodbury|San Luis Obispo|Coconut Creek|Fountainebleau|Tamarac|Diamond Bar|Minnetonka|Taylorsville|Paramount|Weston|Rosemead|Collierville|Highland|Cuyahoga Falls|Huntington Park|Novato|Cathedral City|Greenwood|Joplin|Oak Lawn|Hattiesburg|Bonita Springs|Parker|Eastvale|Lake Elsinore|Watsonville|Bellevue|West Hartford|Manhattan Beach|San Bruno|Hanford|Castle Rock|North Miami|Bullhead City|Kokomo|Burlington|Fort Pierce|Kearny|San Marcos|Kingsport|Leesburg|La Habra|Marlborough|Fond du Lac|Owensboro|Danville|Walnut Creek|Perth Amboy|West New York|Pittsburg|Bothell|Burien|Carol Stream|Romeoville|Woodland|Lakeville|St\. Charles|Lehi|Bozeman|Harrisburg|Hoboken|Yucaipa|Harrison|Lenexa|Sammamish|Fitchburg|Barnstable Town|Keller|Newark|Buffalo Grove|Cedar Falls|Bell Gardens|Lompoc|Belleville|Westfield|Huntsville|Edina|Marana|Gallatin|Woonsocket|West Sacramento|Brunswick|Des Plaines|Minot|Campbell|Moorhead|Painesville|Peabody|Cuyahoga Falls|Midwest City|Hagerstown|Annapolis|Palm Beach Gardens|Hutchinson|Kentwood|Altamonte Springs|Streamwood|New Berlin|Bartlett|Elyria|Castle Rock|Beavercoon|Rome|Dublin|Goldsmith|Hilton Head Island|Middletown|Barnstable Town|Walla Walla|Vestavia Hills|Andover|Gadsden|Edina|Opelika|North Lauderdale|Farmington|Prattville|Grove City|Linden|Franklin|State College|West Bend|Rahway|Klamath Falls|Bentonville|Martinez|Greenfield|Hazleton|Ocoee|Mount Juliet|La Quinta|Crystal Lake|Stockton|Huntsville|Newark|Hoboken|Montclair|Hackensack|Perth Amboy|Sayreville|Linden|Kearny|Bridgeton|Plainfield|Jersey City|Union City|Bayonne|East Orange|Passaic|Clifton|Paterson|Elizabeth|Edison|Woodbridge|Trenton|Camden|Vineland|Millville|Atlantic City|Pleasantville|Ocean City|Somers Point|Northfield|Absecon|Linwood|Collingswood|Haddonfield|Cherry Hill|Moorestown|Mount Laurel|Voorhees|Marlton|Medford|Berlin|Winslow|Gloucester|Washington|Bridgeton|Millville|Vineland|Bridgeton|Cumberland|Salem|Pennsville|Carneys Point|Woodstown|Pilesgrove|Elmer|Upper Pittsgrove|Alloway|Quinton|Olivet|Shiloh|Hopewell|Stow Creek|Greenwich|Cumberland|Lawrence|Maurice River|Downe|Commercial|Fairfield|Lawrence|Millville|Vineland)\b',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                info["location"] = match.group(0)
                break

        return info

    # ==================== ENRICHMENT PIPELINE ====================

    def enrich_profile(self, profile_data: Dict[str, Any]) -> EnrichedContact:
        """Enrich a social media profile with contact info."""
        contact = EnrichedContact()

        # Combine all text fields
        text = " ".join(str(v) for v in profile_data.values() if isinstance(v, str))

        # Extract emails
        emails = self.extract_emails(text)
        if emails:
            contact.email = emails[0]
            contact.confidence_score += 0.3
            contact.sources.append("text_extraction")

        # Extract phones
        phones = self.extract_phones(text)
        if phones:
            contact.phone = self.format_indian_phone(phones[0])
            contact.confidence_score += 0.2
            contact.sources.append("text_extraction")

        # Extract company info
        company_info = self.extract_company_info(text, profile_data.get("bio", ""))
        contact.company = company_info.get("company_name")
        contact.job_title = company_info.get("job_title")
        contact.location = company_info.get("location")
        contact.website = company_info.get("website")

        if contact.company:
            contact.confidence_score += 0.2
        if contact.job_title:
            contact.confidence_score += 0.15

        # Try to find LinkedIn from company + name
        if contact.company and profile_data.get("username"):
            contact.linkedin_url = f"https://linkedin.com/in/{profile_data['username']}"

        # Try to find Twitter
        if profile_data.get("platform") == "twitter":
            contact.twitter_url = f"https://twitter.com/{profile_data.get('username', '')}"

        return contact

    def enrich_batch(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich a batch of profiles."""
        enriched = []

        for profile in profiles:
            contact = self.enrich_profile(profile)

            enriched_profile = {
                **profile,
                "enriched": {
                    "email": contact.email,
                    "phone": contact.phone,
                    "company": contact.company,
                    "job_title": contact.job_title,
                    "location": contact.location,
                    "website": contact.website,
                    "linkedin_url": contact.linkedin_url,
                    "twitter_url": contact.twitter_url,
                    "confidence_score": contact.confidence_score,
                    "sources": contact.sources,
                }
            }
            enriched.append(enriched_profile)

        return enriched

    def enrich_from_website(self, website_url: str) -> Dict[str, Any]:
        """Scrape a website for contact information."""
        info = {
            "emails": [],
            "phones": [],
            "addresses": [],
            "social_links": {},
            "employees": [],
        }

        try:
            response = self.session.get(website_url, timeout=15)
            if response.status_code != 200:
                return info

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()

            # Extract emails
            info["emails"] = self.extract_emails(text)

            # Extract phones
            info["phones"] = self.extract_phones(text)

            # Extract social links
            social_patterns = {
                "linkedin": r'linkedin\.com/[^\s"']+',
                "twitter": r'twitter\.com/[^\s"']+',
                "facebook": r'facebook\.com/[^\s"']+',
                "instagram": r'instagram\.com/[^\s"']+',
                "youtube": r'youtube\.com/[^\s"']+',
            }

            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    info["social_links"][platform] = matches[0]

            # Extract addresses
            address_patterns = [
                r'\d+\s+[A-Za-z0-9\s,.-]+(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Ln|Rd|Blvd|Dr|St)\.?(?:\s+[A-Za-z]+)?,\s*[A-Za-z]+(?:,\s*[A-Z]{2})?\s*\d{5}(?:-\d{4})?',
            ]

            for pattern in address_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                info["addresses"].extend(matches)

            info["addresses"] = list(set(info["addresses"]))[:5]

        except Exception as e:
            logger.error(f"Website enrichment failed for {website_url}: {e}")

        return info

    def verify_email(self, email: str) -> Dict[str, Any]:
        """Verify if an email is valid (basic checks)."""
        result = {
            "email": email,
            "is_valid_format": False,
            "has_mx_record": None,
            "is_disposable": False,
            "is_role_based": False,
        }

        # Format check
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        result["is_valid_format"] = bool(re.match(pattern, email))

        if not result["is_valid_format"]:
            return result

        domain = email.split("@")[1].lower()

        # Check disposable
        disposable_domains = [
            "tempmail.com", "throwaway.com", "mailinator.com", "guerrillamail.com",
            "yopmail.com", "sharklasers.com", "getairmail.com", "10minutemail.com",
        ]
        result["is_disposable"] = domain in disposable_domains

        # Check role-based
        role_prefixes = ["admin", "support", "info", "sales", "marketing", "contact", "help", "team"]
        prefix = email.split("@")[0].lower()
        result["is_role_based"] = any(prefix.startswith(r) for r in role_prefixes)

        return result


# Singleton instance
enrichment_service = DataEnrichmentService()
