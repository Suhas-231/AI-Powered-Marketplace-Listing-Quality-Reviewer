import logging
import re
from typing import List, Dict, Any, Optional
from app.models.policy import Policy
from app.models.listing import Listing

logger = logging.getLogger(__name__)

class PolicyService:
    @staticmethod
    def get_all_active_policies() -> List[Policy]:
        return Policy.query.filter_by(is_active=True).all()

    @classmethod
    def retrieve_relevant_policies(cls, listing: Listing, max_policies: int = 15) -> List[Policy]:
        """
        Retrieves relevant active policies based on listing category and keywords.
        Designed with scoring so that semantic/vector search can be plugged in later.
        """
        active_policies = cls.get_all_active_policies()
        if not active_policies:
            logger.warning("No active policies found in database.")
            return []

        # If total active policies is small (e.g. <= 20), supply all active policies
        # so AI reviewer has complete policy rule coverage.
        if len(active_policies) <= max_policies:
            return active_policies

        # Scoring mechanism for larger policy knowledge bases
        combined_text = f"{listing.title} {listing.description} {listing.category} {' '.join(listing.tags or [])}".lower()
        
        scored = []
        for pol in active_policies:
            score = 1  # Base score

            # Category relevance
            pol_cat_lower = pol.category.lower()
            list_cat_lower = listing.category.lower()
            if "general" in pol_cat_lower or "title" in pol_cat_lower or "description" in pol_cat_lower:
                score += 3
            if pol_cat_lower in list_cat_lower or list_cat_lower in pol_cat_lower:
                score += 5

            # Keyword matching from policy title and description
            keywords = re.findall(r'\b\w{4,}\b', (pol.title + " " + pol.description).lower())
            for kw in set(keywords):
                if kw in combined_text:
                    score += 2

            scored.append((score, pol))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [pol for _, pol in scored[:max_policies]]

    @staticmethod
    def format_policies_for_prompt(policies: List[Policy]) -> str:
        """
        Formats policy records into a clear, structured prompt context for AI policy review.
        """
        if not policies:
            return "NO POLICIES SUPPLIED. Explicitly state that no applicable policy was found."

        formatted_lines = []
        for pol in policies:
            demo_tag = "[DEMONSTRATION POLICY]" if pol.is_demo_policy else "[VERIFIED POLICY]"
            formatted_lines.append(
                f"- Policy Code: {pol.policy_code} | Section: {pol.section_number} {demo_tag}\n"
                f"  Title: {pol.title}\n"
                f"  Category: {pol.category}\n"
                f"  Severity Guidance: {pol.severity_guidance}\n"
                f"  Rule Description: {pol.description}\n"
            )
        return "\n".join(formatted_lines)

    @classmethod
    def verify_policy_citations(cls, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates whether policy sections cited by the AI exist in the database.
        Prevents hallucinated policy codes from creating invalid relations.
        """
        # Map codes to policies
        all_policies = Policy.query.all()
        policy_map = {p.policy_code.strip().upper(): p for p in all_policies}
        # Also map title fragments or section numbers
        section_map = {p.section_number.strip().upper(): p for p in all_policies}

        verified_findings = []
        for finding in findings:
            raw_code = finding.get("policy_section") or finding.get("policy_code") or ""
            raw_code_clean = str(raw_code).strip().upper()

            matched_policy = policy_map.get(raw_code_clean)
            if not matched_policy and raw_code_clean in section_map:
                matched_policy = section_map[raw_code_clean]

            # Try partial matching if code is in string
            if not matched_policy:
                for code, p in policy_map.items():
                    if code in raw_code_clean:
                        matched_policy = p
                        break

            finding_copy = dict(finding)
            if matched_policy:
                finding_copy["policy_id"] = matched_policy.id
                finding_copy["policy_reference_code"] = matched_policy.policy_code
                finding_copy["policy_reference_text"] = matched_policy.title
                finding_copy["citation_verified"] = True
            else:
                logger.warning(f"Unverified or hallucinated policy citation from AI: '{raw_code}'")
                finding_copy["policy_id"] = None
                finding_copy["policy_reference_code"] = raw_code if raw_code else "UNKNOWN-POLICY"
                finding_copy["policy_reference_text"] = "Unverified Citation (Not in policy database)"
                finding_copy["citation_verified"] = False

            verified_findings.append(finding_copy)

        return verified_findings
