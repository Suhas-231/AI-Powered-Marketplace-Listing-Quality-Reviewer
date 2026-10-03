import json
import logging
import os
import re
import time
from typing import Dict, Any, List
from flask import current_app
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a professional Marketplace Listing Quality Reviewer.

Review product and service listings against the supplied marketplace policy and brand-content guidelines.

Identify unclear, misleading, prohibited or incomplete content.

For each finding:
1. Identify the affected field.
2. Quote the problematic original content.
3. Explain the problem.
4. Assign severity: Low, Medium or High.
5. Cite the exact supplied policy section when applicable (e.g., POL-TITLE-001, POL-HLTH-001).
6. Suggest improved wording.
7. Explain why the revision improves the listing.
8. Identify assumptions or unverifiable claims.

Never invent policy references.
Never treat a suggestion as an approved revision.
Never automatically approve or publish a listing.
If no applicable policy is supplied, explicitly state that fact.

Return structured JSON only matching this schema:
{
  "overall_status": "needs_review" | "flagged" | "compliant",
  "summary": "Summary of the review",
  "findings": [
    {
      "field": "title" | "description" | "price" | "attributes" | "seller" | "tags",
      "original_value": "Original listing content that triggered the finding",
      "issue_type": "misleading_claim" | "prohibited_content" | "unclear_content" | "keyword_stuffing" | "unverifiable_claim" | "off_platform_redirect" | "counterfeit_trademark" | "formatting_violation",
      "severity": "High" | "Medium" | "Low",
      "issue": "Explanation of the issue",
      "policy_section": "POL-XXX-000",
      "policy_reference": "Policy title or description reference",
      "suggested_revision": "Improved content to replace original value",
      "explanation": "Reason for suggested improvement",
      "requires_human_review": true
    }
  ],
  "assumptions": ["string"],
  "unverifiable_claims": ["string"],
  "policy_coverage": "sample_policy"
}
"""

class GeminiService:
    @classmethod
    def get_client(cls):
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in backend environment.")
        return genai.Client(api_key=api_key)

    @classmethod
    def analyze_listing(cls, listing_data: Dict[str, Any], policies_context: str) -> Dict[str, Any]:
        """
        Calls Gemini to review listing against retrieved policies.
        Includes retry logic, JSON cleaning/validation, and structured error handling.
        """
        api_key = current_app.config.get("GEMINI_API_KEY")
        model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")

        # Prepare user prompt
        listing_json_str = json.dumps(listing_data, indent=2)
        user_prompt = f"""EVALUATION REQUEST:
Please review the following marketplace listing against the supplied demonstration policies.

--- SUPPLIED POLICIES ---
{policies_context}

--- LISTING TO REVIEW ---
{listing_json_str}

Review every field carefully (title, description, price, attributes, seller, tags).
Identify all violations of the supplied policies or content-quality problems.
Provide compliant, professionally rewritten replacement wording for each finding.
Return JSON ONLY.
"""

        # In testing or when mock key is provided
        if current_app.config.get("TESTING") and api_key == "test-mock-key":
            return cls._generate_mock_analysis(listing_data)

        if not api_key or api_key == "your_gemini_api_key_here":
            logger.error("Gemini API key is not configured or placeholder.")
            raise ValueError("Gemini API key is not configured. Please add GEMINI_API_KEY to your backend .env file.")

        logger.info(f"Initiating AI review for listing '{listing_data.get('title')[:30]}...' using model {model_name}")
        client = cls.get_client()

        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )

                raw_text = response.text
                if not raw_text:
                    raise ValueError("Gemini API returned an empty response.")

                parsed_json = cls._clean_and_parse_json(raw_text)
                validated_review = cls._validate_review_schema(parsed_json)
                logger.info(f"AI review completed successfully with {len(validated_review.get('findings', []))} findings.")
                return validated_review

            except APIError as api_err:
                last_error = api_err
                logger.warning(f"Gemini API error on attempt {attempt + 1}: {api_err}")
                if "RESOURCE_EXHAUSTED" in str(api_err) or "429" in str(api_err):
                    time.sleep(2 * (attempt + 1))
                elif attempt == max_retries:
                    raise api_err
            except json.JSONDecodeError as json_err:
                last_error = json_err
                logger.warning(f"Failed to parse Gemini JSON on attempt {attempt + 1}: {json_err}")
                if attempt == max_retries:
                    raise ValueError(f"AI returned invalid JSON format: {str(json_err)}")
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error communicating with Gemini on attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    raise e
                time.sleep(1)

        raise last_error or RuntimeError("Gemini API request failed after retries.")

    @classmethod
    def _clean_and_parse_json(cls, raw_text: str) -> Dict[str, Any]:
        """Cleans Markdown code fence delimiters and extracts valid JSON."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Find outer JSON braces if extra text exists
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx:end_idx+1]

        return json.loads(cleaned)

    @classmethod
    def _validate_review_schema(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all required review fields and finding schemas exist."""
        if not isinstance(data, dict):
            raise ValueError("Review payload must be a JSON object.")

        overall_status = data.get("overall_status", "needs_review")
        if overall_status not in ["needs_review", "flagged", "compliant"]:
            overall_status = "needs_review"

        summary = data.get("summary") or "Listing review completed against demonstration policy library."
        raw_findings = data.get("findings", [])
        clean_findings = []

        if isinstance(raw_findings, list):
            for idx, f in enumerate(raw_findings):
                if not isinstance(f, dict):
                    continue
                clean_finding = {
                    "field": f.get("field", "description"),
                    "original_value": str(f.get("original_value", "")),
                    "issue_type": f.get("issue_type", "policy_violation"),
                    "severity": str(f.get("severity", "Medium")).capitalize(),
                    "issue": f.get("issue") or f.get("explanation") or "Policy non-compliance identified.",
                    "policy_section": str(f.get("policy_section", "")).strip(),
                    "policy_reference": str(f.get("policy_reference", "")).strip(),
                    "suggested_revision": str(f.get("suggested_revision", "")).strip(),
                    "explanation": str(f.get("explanation", "")).strip(),
                    "requires_human_review": bool(f.get("requires_human_review", True))
                }
                # Normalize severity
                if clean_finding["severity"] not in ["High", "Medium", "Low"]:
                    clean_finding["severity"] = "Medium"

                clean_findings.append(clean_finding)

        return {
            "overall_status": overall_status,
            "summary": summary,
            "findings": clean_findings,
            "assumptions": data.get("assumptions", []),
            "unverifiable_claims": data.get("unverifiable_claims", []),
            "policy_coverage": data.get("policy_coverage", "sample_policy")
        }

    @classmethod
    def _generate_mock_analysis(cls, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provides deterministic mock analysis for test suites without external network calls."""
        title = listing_data.get("title", "")
        desc = listing_data.get("description", "")
        findings = []

        if "cure" in title.lower() or "miracle" in title.lower() or "cancer" in title.lower() or "diabetes" in title.lower():
            findings.append({
                "field": "title",
                "original_value": title,
                "issue_type": "misleading_claim",
                "severity": "High",
                "issue": "Title contains prohibited medical cure and miraculous health claims.",
                "policy_section": "POL-HLTH-001",
                "policy_reference": "Medical, Therapeutic & Disease-Cure Claims",
                "suggested_revision": "Herbal Wellness Tea - Natural Botanical Blend (Loose Leaf)",
                "explanation": "Removed non-compliant therapeutic promises and exaggerated disease treatment claims.",
                "requires_human_review": True
            })

        if "whatsapp" in desc.lower() or "http" in desc.lower() or "+1" in desc.lower():
            findings.append({
                "field": "description",
                "original_value": desc,
                "issue_type": "off_platform_redirect",
                "severity": "High",
                "issue": "Description directs buyers to off-platform channels and external URLs.",
                "policy_section": "POL-DESC-002",
                "policy_reference": "Prohibition of Off-Platform Redirection",
                "suggested_revision": "Premium herbal blend crafted with carefully selected botanicals. Enjoy refreshing natural flavor with every cup.",
                "explanation": "Stripped off-platform contact numbers and external links in compliance with marketplace redirection policies.",
                "requires_human_review": True
            })

        if not findings:
            findings.append({
                "field": "description",
                "original_value": desc,
                "issue_type": "formatting_violation",
                "severity": "Low",
                "issue": "Consider structuring product specifications into bullet points for readability.",
                "policy_section": "POL-DESC-001",
                "policy_reference": "Description Clarity & Truthful Representation",
                "suggested_revision": desc,
                "explanation": "Formatting enhancement suggestion.",
                "requires_human_review": False
            })

        return {
            "overall_status": "flagged" if any(f["severity"] == "High" for f in findings) else "needs_review",
            "summary": "Mock policy analysis identified potential compliance issues.",
            "findings": findings,
            "assumptions": ["Assumed product is an uncertified herbal commodity."],
            "unverifiable_claims": ["Claims of rapid cure or infinite lifespan."],
            "policy_coverage": "sample_policy"
        }
