"""Lead scoring and dynamic pricing engine."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import math

from app.core.logging import logger


class LeadQuality(str, Enum):
    COLD = "cold"
    WARM = "warm" 
    HOT = "hot"
    PREMIUM = "premium"


@dataclass
class LeadScore:
    """Lead scoring result."""
    score: float  # 0-100
    quality: LeadQuality
    factors: Dict[str, float]
    estimated_value: float
    recommendations: List[str]


class LeadScoringEngine:
    """AI-powered lead scoring engine."""

    # Scoring weights
    WEIGHTS = {
        "profile_completeness": 0.15,
        "engagement_level": 0.20,
        "contact_availability": 0.25,
        "company_signal": 0.15,
        "intent_signal": 0.15,
        "recency": 0.10,
    }

    def __init__(self):
        self.quality_thresholds = {
            LeadQuality.COLD: (0, 40),
            LeadQuality.WARM: (40, 60),
            LeadQuality.HOT: (60, 80),
            LeadQuality.PREMIUM: (80, 100),
        }

    def score_lead(self, lead_data: Dict[str, Any]) -> LeadScore:
        """Score a single lead."""
        factors = {}

        # 1. Profile Completeness (0-100)
        factors["profile_completeness"] = self._score_profile_completeness(lead_data)

        # 2. Engagement Level (0-100)
        factors["engagement_level"] = self._score_engagement(lead_data)

        # 3. Contact Availability (0-100)
        factors["contact_availability"] = self._score_contact_availability(lead_data)

        # 4. Company Signal (0-100)
        factors["company_signal"] = self._score_company_signal(lead_data)

        # 5. Intent Signal (0-100)
        factors["intent_signal"] = self._score_intent(lead_data)

        # 6. Recency (0-100)
        factors["recency"] = self._score_recency(lead_data)

        # Calculate weighted score
        total_score = sum(
            factors[key] * self.WEIGHTS[key]
            for key in factors
        )

        # Determine quality
        quality = self._get_quality(total_score)

        # Estimate value
        estimated_value = self._estimate_value(total_score, lead_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(factors, lead_data)

        return LeadScore(
            score=round(total_score, 2),
            quality=quality,
            factors=factors,
            estimated_value=round(estimated_value, 2),
            recommendations=recommendations,
        )

    def _score_profile_completeness(self, lead: Dict[str, Any]) -> float:
        """Score based on how complete the profile is."""
        score = 0
        checks = [
            ("username", 10),
            ("display_name", 10),
            ("bio", 15),
            ("location", 15),
            ("followers_count", 10),
            ("is_verified", 20),
            ("profile_pic_url", 10),
            ("external_url", 10),
        ]

        for field, points in checks:
            value = lead.get(field)
            if value and value not in [None, "", 0, False]:
                score += points

        return min(score, 100)

    def _score_engagement(self, lead: Dict[str, Any]) -> float:
        """Score based on social engagement metrics."""
        followers = lead.get("followers_count", 0) or 0
        following = lead.get("following_count", 0) or 1
        posts = lead.get("posts_count", 0) or 0

        # Follower ratio (quality indicator)
        ratio = followers / max(following, 1)
        ratio_score = min(ratio * 20, 40)

        # Follower count tiers
        if followers >= 100000:
            follower_score = 40
        elif followers >= 10000:
            follower_score = 30
        elif followers >= 1000:
            follower_score = 20
        elif followers >= 100:
            follower_score = 10
        else:
            follower_score = 5

        # Activity level
        if posts >= 100:
            activity_score = 20
        elif posts >= 50:
            activity_score = 15
        elif posts >= 10:
            activity_score = 10
        else:
            activity_score = 5

        return min(ratio_score + follower_score + activity_score, 100)

    def _score_contact_availability(self, lead: Dict[str, Any]) -> float:
        """Score based on available contact methods."""
        score = 0

        enriched = lead.get("enriched", {})

        if enriched.get("email"):
            score += 40
        if enriched.get("phone"):
            score += 30
        if lead.get("external_url") or enriched.get("website"):
            score += 20
        if enriched.get("linkedin_url"):
            score += 10

        return min(score, 100)

    def _score_company_signal(self, lead: Dict[str, Any]) -> float:
        """Score based on company/employment signals."""
        score = 0
        enriched = lead.get("enriched", {})

        company = enriched.get("company")
        job_title = enriched.get("job_title")

        if company:
            score += 40
            # Bonus for known companies
            known_companies = [
                "google", "microsoft", "amazon", "apple", "meta", "facebook",
                "netflix", "tesla", "adobe", "salesforce", "oracle", "ibm",
                "infosys", "tcs", "wipro", "hcl", "tech mahindra", "cognizant",
                "accenture", "deloitte", "pwc", "ey", "kpmg",
            ]
            if any(known in company.lower() for known in known_companies):
                score += 20

        if job_title:
            score += 20
            # Bonus for decision-maker titles
            decision_titles = [
                "ceo", "cto", "cfo", "coo", "cmo", "founder", "co-founder",
                "director", "vp", "vice president", "head of", "manager",
                "principal", "lead", "senior",
            ]
            if any(title in job_title.lower() for title in decision_titles):
                score += 20

        return min(score, 100)

    def _score_intent(self, lead: Dict[str, Any]) -> float:
        """Score based on buying intent signals."""
        score = 0
        content = lead.get("post_content", "") or ""
        bio = lead.get("bio", "") or ""
        combined = f"{content} {bio}".lower()

        # High intent keywords
        high_intent = [
            "looking for", "seeking", "hiring", "recruiting", "job opening",
            "vacancy", "position available", "we are hiring", "join our team",
            "budget", "investment", "funding", "raise", "series",
            "expanding", "growing", "scaling", "new office", "launching",
        ]

        # Medium intent keywords
        medium_intent = [
            "interested in", "considering", "evaluating", "researching",
            "comparing", "review", "feedback", "suggestion",
        ]

        for keyword in high_intent:
            if keyword in combined:
                score += 15

        for keyword in medium_intent:
            if keyword in combined:
                score += 8

        # Recent job change signal
        if any(word in combined for word in ["new role", "started", "joined", "excited to announce"]):
            score += 20

        return min(score, 100)

    def _score_recency(self, lead: Dict[str, Any]) -> float:
        """Score based on how recent the data is."""
        from datetime import datetime, timedelta

        posted_at = lead.get("posted_at")
        if not posted_at:
            return 50  # Neutral if no date

        try:
            if isinstance(posted_at, str):
                posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))

            age = datetime.utcnow() - posted_at

            if age <= timedelta(days=1):
                return 100
            elif age <= timedelta(days=7):
                return 90
            elif age <= timedelta(days=30):
                return 75
            elif age <= timedelta(days=90):
                return 60
            elif age <= timedelta(days=180):
                return 40
            else:
                return 20

        except Exception:
            return 50

    def _get_quality(self, score: float) -> LeadQuality:
        """Determine lead quality from score."""
        for quality, (min_score, max_score) in self.quality_thresholds.items():
            if min_score <= score < max_score:
                return quality
        return LeadQuality.PREMIUM

    def _estimate_value(self, score: float, lead: Dict[str, Any]) -> float:
        """Estimate monetary value of the lead."""
        base_value = 5  # Base value in INR

        # Multiplier based on score
        multiplier = 1 + (score / 100) * 4  # 1x to 5x

        # Bonus for verified accounts
        if lead.get("is_verified"):
            multiplier *= 1.5

        # Bonus for high engagement
        followers = lead.get("followers_count", 0) or 0
        if followers >= 100000:
            multiplier *= 2.0
        elif followers >= 10000:
            multiplier *= 1.5

        return base_value * multiplier

    def _generate_recommendations(self, factors: Dict[str, float], lead: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if factors["contact_availability"] < 50:
            recommendations.append("Try finding email via LinkedIn or company website")

        if factors["engagement_level"] < 40:
            recommendations.append("Low engagement - may not be active on this platform")

        if factors["intent_signal"] > 60:
            recommendations.append("High intent detected - prioritize outreach")

        if factors["company_signal"] > 70:
            recommendations.append("Decision maker identified - high-value target")

        if factors["recency"] < 40:
            recommendations.append("Data is old - verify current status before outreach")

        if not recommendations:
            recommendations.append("Standard outreach recommended")

        return recommendations

    def score_batch(self, leads: List[Dict[str, Any]]) -> List[LeadScore]:
        """Score a batch of leads."""
        return [self.score_lead(lead) for lead in leads]


class PricingEngine:
    """Dynamic pricing engine for data products."""

    # Base prices per lead by quality
    BASE_PRICES = {
        LeadQuality.COLD: 2.0,
        LeadQuality.WARM: 5.0,
        LeadQuality.HOT: 12.0,
        LeadQuality.PREMIUM: 25.0,
    }

    # Platform multipliers
    PLATFORM_MULTIPLIERS = {
        "linkedin": 2.0,
        "twitter": 1.2,
        "instagram": 0.8,
        "reddit": 0.6,
        "youtube": 0.7,
        "facebook": 0.9,
        "pinterest": 0.5,
        "google_search": 0.4,
    }

    # Industry multipliers
    INDUSTRY_MULTIPLIERS = {
        "technology": 1.5,
        "finance": 1.4,
        "healthcare": 1.3,
        "ecommerce": 1.2,
        "education": 0.8,
        "real_estate": 1.1,
        "saas": 1.6,
        "b2b": 1.3,
        "b2c": 0.9,
        "startup": 1.4,
    }

    def __init__(self):
        self.scoring_engine = LeadScoringEngine()

    def calculate_lead_price(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate price for a single lead."""
        score = self.scoring_engine.score_lead(lead)

        base_price = self.BASE_PRICES[score.quality]

        # Apply platform multiplier
        platform = lead.get("platform", "unknown")
        platform_mult = self.PLATFORM_MULTIPLIERS.get(platform, 1.0)

        # Apply industry multiplier
        enriched = lead.get("enriched", {})
        industry = "general"
        for ind, mult in self.INDUSTRY_MULTIPLIERS.items():
            if ind in str(enriched.get("company", "")).lower():
                industry = ind
                break
        industry_mult = self.INDUSTRY_MULTIPLIERS.get(industry, 1.0)

        # Apply enrichment bonus
        enrichment_bonus = 1.0
        if enriched.get("email"):
            enrichment_bonus += 0.3
        if enriched.get("phone"):
            enrichment_bonus += 0.2
        if enriched.get("company"):
            enrichment_bonus += 0.15

        final_price = base_price * platform_mult * industry_mult * enrichment_bonus

        return {
            "lead_id": lead.get("source_id", "unknown"),
            "base_price": base_price,
            "platform_multiplier": platform_mult,
            "industry_multiplier": industry_mult,
            "enrichment_bonus": enrichment_bonus,
            "final_price_per_lead": round(final_price, 2),
            "quality": score.quality.value,
            "score": score.score,
            "estimated_value": score.estimated_value,
        }

    def calculate_package_price(
        self,
        leads: List[Dict[str, Any]],
        package_type: str = "mixed",
        volume_discount: bool = True,
    ) -> Dict[str, Any]:
        """Calculate price for a package of leads."""

        lead_prices = []
        total_base = 0

        quality_counts = {q: 0 for q in LeadQuality}

        for lead in leads:
            price_info = self.calculate_lead_price(lead)
            lead_prices.append(price_info)
            total_base += price_info["final_price_per_lead"]

            quality = LeadQuality(price_info["quality"])
            quality_counts[quality] += 1

        # Volume discount
        volume_discount_rate = 0
        if volume_discount:
            count = len(leads)
            if count >= 10000:
                volume_discount_rate = 0.30
            elif count >= 5000:
                volume_discount_rate = 0.25
            elif count >= 1000:
                volume_discount_rate = 0.20
            elif count >= 500:
                volume_discount_rate = 0.15
            elif count >= 100:
                volume_discount_rate = 0.10
            elif count >= 50:
                volume_discount_rate = 0.05

        discounted_total = total_base * (1 - volume_discount_rate)

        # Add GST (18%)
        gst = discounted_total * 0.18
        final_total = discounted_total + gst

        return {
            "package_type": package_type,
            "total_leads": len(leads),
            "quality_breakdown": {
                q.value: count for q, count in quality_counts.items()
            },
            "base_price": round(total_base, 2),
            "volume_discount_rate": volume_discount_rate,
            "volume_discount_amount": round(total_base * volume_discount_rate, 2),
            "discounted_price": round(discounted_total, 2),
            "gst_18_percent": round(gst, 2),
            "final_total_inr": round(final_total, 2),
            "price_per_lead_avg": round(final_total / len(leads), 2) if leads else 0,
            "lead_details": lead_prices[:10],  # First 10 for preview
        }

    def get_pricing_tiers(self) -> List[Dict[str, Any]]:
        """Get standard pricing tiers."""
        return [
            {
                "name": "Starter",
                "min_leads": 50,
                "max_leads": 499,
                "price_per_lead": "₹3-8",
                "discount": "5%",
                "features": [
                    "Basic contact info",
                    "Email verification",
                    "CSV export",
                    "Standard support",
                ],
            },
            {
                "name": "Professional",
                "min_leads": 500,
                "max_leads": 999,
                "price_per_lead": "₹2.5-7",
                "discount": "15%",
                "features": [
                    "Full contact enrichment",
                    "Phone numbers",
                    "Company info",
                    "Lead scoring",
                    "Excel + CSV export",
                    "Priority support",
                ],
            },
            {
                "name": "Business",
                "min_leads": 1000,
                "max_leads": 4999,
                "price_per_lead": "₹2-6",
                "discount": "20%",
                "features": [
                    "Everything in Professional",
                    "API access",
                    "Real-time updates",
                    "Custom filters",
                    "Dedicated account manager",
                ],
            },
            {
                "name": "Enterprise",
                "min_leads": 5000,
                "max_leads": None,
                "price_per_lead": "Custom",
                "discount": "25-30%",
                "features": [
                    "Everything in Business",
                    "White-label options",
                    "Custom integrations",
                    "SLA guarantee",
                    "On-premise deployment",
                ],
            },
        ]


# Singleton instances
lead_scoring_engine = LeadScoringEngine()
pricing_engine = PricingEngine()
