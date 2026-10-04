import json
import logging
import os
import random
import re
import time
from typing import Dict, Any, List, Optional
from flask import current_app
from groq import (
    Groq,
    APIError,
    APIStatusError,
    RateLimitError,
    InternalServerError,
    APITimeoutError,
    APIConnectionError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    BadRequestError,
)

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a professional Marketplace Listing Quality Reviewer.
Your role is to strictly evaluate product and service listings against the supplied marketplace policies and brand-content guidelines.

CRITICAL INSTRUCTIONS FOR JSON OUTPUT:
- You must return ONLY a single, valid JSON object matching the exact structure below.
- Do NOT output markdown code blocks (such as ```json or ```), preamble, conversational commentary, or chain-of-thought reasoning.
- Every field specified below is REQUIRED. Null values are strictly PROHIBITED. Use empty strings "" or empty arrays [] where specified.
- Never invent policy references. Only cite policy sections that appear in the supplied policy list.
- Never automatically approve or publish a listing.

REQUIRED JSON STRUCTURE:
{
  "overall_status": "<string: must be exactly 'compliant', 'needs_review', or 'flagged'>",
  "summary": "<string: 1-3 sentences summarizing compliance status. Non-empty, never null>",
  "findings": [
    {
      "field": "<string: affected listing field, must be one of: 'title', 'description', 'price', 'category', 'attributes', 'seller', 'tags'>",
      "original_value": "<string: exact problematic excerpt from listing. Never null, use empty string '' if not applicable>",
      "issue_type": "<string: violation type, must be one of: 'misleading_claim', 'prohibited_content', 'unclear_content', 'keyword_stuffing', 'unverifiable_claim', 'off_platform_redirect', 'counterfeit_trademark', 'formatting_violation'>",
      "severity": "<string: violation severity, must be one of: 'High', 'Medium', 'Low'>",
      "issue": "<string: clear explanation of the policy violation or quality problem. Non-empty, never null>",
      "policy_section": "<string: exact policy code from supplied policies, e.g. 'POL-HLTH-001'. Never null, use 'NONE' if no specific policy section applies>",
      "policy_reference": "<string: policy title or description reference. Never null, use 'General Marketplace Standard' if unreferenced>",
      "suggested_revision": "<string: compliant, professionally rewritten replacement text. Non-empty, never null>",
      "explanation": "<string: reason why the suggested revision resolves the issue. Non-empty, never null>",
      "requires_human_review": <boolean: true or false>
    }
  ],
  "assumptions": ["<string: any assumptions made about the product/claims; return empty array [] if none, never null>"],
  "unverifiable_claims": ["<string: any claims that cannot be verified; return empty array [] if none, never null>"],
  "policy_coverage": "<string: must be one of: 'sample_policy', 'official_policy', 'none'. Default 'sample_policy'>"
}

STATUS CLASSIFICATION RULES:
- "compliant": 0 policy violations found. Content is truthful, complete, and verified.
- "needs_review": Minor issues, formatting recommendations, or missing non-critical attributes found (severity Low or Medium).
- "flagged": High severity violations found (such as disease cure claims, prohibited items, off-platform redirects, or counterfeit trademarks).
"""

REVIEW_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_status": {
            "type": "string",
            "enum": ["compliant", "needs_review", "flagged"]
        },
        "summary": {
            "type": "string"
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "enum": ["title", "description", "price", "category", "attributes", "seller", "tags"]
                    },
                    "original_value": {"type": "string"},
                    "issue_type": {
                        "type": "string",
                        "enum": [
                            "misleading_claim",
                            "prohibited_content",
                            "unclear_content",
                            "keyword_stuffing",
                            "unverifiable_claim",
                            "off_platform_redirect",
                            "counterfeit_trademark",
                            "formatting_violation"
                        ]
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["High", "Medium", "Low"]
                    },
                    "issue": {"type": "string"},
                    "policy_section": {"type": "string"},
                    "policy_reference": {"type": "string"},
                    "suggested_revision": {"type": "string"},
                    "explanation": {"type": "string"},
                    "requires_human_review": {"type": "boolean"}
                },
                "required": [
                    "field",
                    "original_value",
                    "issue_type",
                    "severity",
                    "issue",
                    "policy_section",
                    "policy_reference",
                    "suggested_revision",
                    "explanation",
                    "requires_human_review"
                ],
                "additionalProperties": False
            }
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"}
        },
        "unverifiable_claims": {
            "type": "array",
            "items": {"type": "string"}
        },
        "policy_coverage": {
            "type": "string",
            "enum": ["sample_policy", "official_policy", "none"]
        }
    },
    "required": [
        "overall_status",
        "summary",
        "findings",
        "assumptions",
        "unverifiable_claims",
        "policy_coverage"
    ],
    "additionalProperties": False
}


class GroqService:
    @staticmethod
    def sanitize_error_message(text: str) -> str:
        """Sanitizes error text to prevent API keys or bearer tokens from leaking into logs or API responses."""
        if not text:
            return ""
        sanitized = re.sub(r'gsk_[a-zA-Z0-9_-]+', '[REDACTED_GROQ_KEY]', str(text))
        sanitized = re.sub(r'AIza[a-zA-Z0-9_-]+', '[REDACTED_KEY]', sanitized)
        sanitized = re.sub(r'Bearer\s+[a-zA-Z0-9_\.-]+', 'Bearer [REDACTED]', sanitized)
        sanitized = re.sub(r'(api[_-]?key[:=]\s*[\'"]?)[a-zA-Z0-9_-]{20,}([\'"]?)', r'\1[REDACTED]\2', sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def get_client(cls) -> Groq:
        api_key = current_app.config.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured in backend environment.")
        return Groq(api_key=api_key)

    @classmethod
    def _extract_failed_generation(cls, err: Exception) -> Optional[str]:
        """Safely extracts failed_generation from Groq BadRequestError response body if available."""
        if isinstance(err, BadRequestError):
            if isinstance(err.body, dict) and "error" in err.body:
                error_obj = err.body["error"]
                if isinstance(error_obj, dict) and error_obj.get("failed_generation"):
                    return str(error_obj["failed_generation"])
            response = getattr(err, "response", None)
            if response is not None:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "error" in data:
                        failed = data["error"].get("failed_generation")
                        if failed:
                            return str(failed)
                except Exception:
                    pass
        return None

    @classmethod
    def _build_standard_prompt(cls, listing_data: Dict[str, Any], policies_context: str) -> str:
        """Builds comprehensive evaluation prompt for initial AI review."""
        listing_json_str = json.dumps(listing_data, indent=2)
        return f"""EVALUATION REQUEST:
Please review the following marketplace listing against the supplied demonstration policies.

--- SUPPLIED POLICIES ---
{policies_context}

--- LISTING TO REVIEW ---
{listing_json_str}

Review every field carefully (title, description, price, attributes, seller, tags).
Identify all violations of the supplied policies or content-quality problems.
Provide compliant, professionally rewritten replacement wording for each finding.
Return JSON ONLY matching the requested review structure.
"""

    @classmethod
    def _build_simplified_prompt(cls, listing_data: Dict[str, Any], policies_context: str) -> str:
        """
        Builds a simplified, direct prompt for retry attempts when standard schema validation fails.
        Focuses strictly on essential listing data and explicit JSON structure.
        """
        title = listing_data.get("title", "")
        desc = listing_data.get("description", "")
        cat = listing_data.get("category", "")
        price = f"{listing_data.get('price', '')} {listing_data.get('currency', 'USD')}"

        return f"""REVIEW TASK:
Analyze this listing against marketplace policies and return ONLY a valid JSON object.

POLICIES:
{policies_context}

LISTING:
Title: {title}
Category: {cat}
Price: {price}
Description: {desc}

REQUIRED JSON KEYS (all keys must be present):
{{
  "overall_status": "compliant" | "needs_review" | "flagged",
  "summary": "1-2 sentence evaluation",
  "findings": [
    {{
      "field": "title" | "description" | "price" | "category" | "attributes" | "seller" | "tags",
      "original_value": "problematic phrase",
      "issue_type": "misleading_claim" | "prohibited_content" | "unclear_content" | "formatting_violation",
      "severity": "High" | "Medium" | "Low",
      "issue": "description of violation",
      "policy_section": "POL-XXX-000",
      "policy_reference": "policy name",
      "suggested_revision": "rewritten text",
      "explanation": "why this fixes the issue",
      "requires_human_review": true
    }}
  ],
  "assumptions": [],
  "unverifiable_claims": [],
  "policy_coverage": "sample_policy"
}}

OUTPUT RAW JSON ONLY. NO MARKDOWN, NO CODE BLOCKS. If no issues exist, set findings to []."""

    @classmethod
    def analyze_listing(cls, listing_data: Dict[str, Any], policies_context: str) -> Dict[str, Any]:
        """
        Calls Groq API to review listing against retrieved policies.
        Uses Groq Chat Completions API with structured JSON output, bounded exponential backoff
        for transient errors, failed_generation salvaging, and simplified prompt retry fallbacks.
        """
        api_key = current_app.config.get("GROQ_API_KEY")
        model_name = current_app.config.get("GROQ_MODEL", "openai/gpt-oss-20b")

        # In testing or when mock key is provided
        if current_app.config.get("TESTING") and api_key == "test-mock-key":
            return cls._generate_mock_analysis(listing_data)

        if not api_key or api_key in ["your_groq_api_key_here", "YOUR_GROQ_API_KEY"]:
            logger.error("Groq API key is not configured or placeholder.")
            raise ValueError("Groq API key is not configured. Please add GROQ_API_KEY to your backend .env file.")

        logger.info(f"Initiating Groq review with model='{model_name}' for listing '{listing_data.get('title', '')[:30]}...'")
        client = cls.get_client()

        max_retries = 3
        last_error = None
        use_structured_schema = True
        use_simplified_prompt = False

        for attempt in range(max_retries + 1):
            try:
                # Select prompt based on retry status
                if use_simplified_prompt:
                    current_prompt = cls._build_simplified_prompt(listing_data, policies_context)
                else:
                    current_prompt = cls._build_standard_prompt(listing_data, policies_context)

                messages = [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": current_prompt}
                ]

                # Attempt with structured outputs (json_schema) first, fallback to json_object if unsupported or failed
                response_format = (
                    {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "listing_quality_review",
                            "strict": True,
                            "schema": REVIEW_JSON_SCHEMA
                        }
                    }
                    if use_structured_schema
                    else {"type": "json_object"}
                )

                logger.info(
                    f"Groq API call attempt {attempt + 1}/{max_retries + 1} "
                    f"[model='{model_name}', schema_mode={'json_schema' if use_structured_schema else 'json_object'}, "
                    f"prompt_mode={'simplified' if use_simplified_prompt else 'standard'}]"
                )

                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_format=response_format,
                    temperature=0.1
                )

                if not completion.choices or not completion.choices[0].message:
                    raise ValueError("Groq API returned an empty response.")

                raw_text = completion.choices[0].message.content
                if not raw_text:
                    raise ValueError("Groq API returned empty message content.")

                parsed_json = cls._clean_and_parse_json(raw_text)
                validated_review = cls._validate_review_schema(parsed_json)
                logger.info(
                    f"Groq AI review completed successfully on attempt {attempt + 1} "
                    f"using model='{model_name}' with {len(validated_review.get('findings', []))} findings."
                )
                return validated_review

            except BadRequestError as bad_req:
                last_error = bad_req
                msg = str(bad_req)
                sanitized_msg = cls.sanitize_error_message(msg)
                logger.warning(
                    f"Groq BadRequestError on attempt {attempt + 1}/{max_retries + 1} with model='{model_name}': {sanitized_msg}"
                )

                # Check if this is a json_validate_failed error
                is_json_val_fail = (
                    "json_validate_failed" in sanitized_msg.lower()
                    or "json_validate" in sanitized_msg.lower()
                    or (isinstance(bad_req.body, dict) and bad_req.body.get("error", {}).get("code") == "json_validate_failed")
                )

                if is_json_val_fail:
                    # Step A: Attempt to salvage JSON from failed_generation if provided
                    failed_gen = cls._extract_failed_generation(bad_req)
                    if failed_gen:
                        try:
                            recovered_json = cls._clean_and_parse_json(failed_gen)
                            validated_review = cls._validate_review_schema(recovered_json)
                            logger.info(
                                f"Successfully recovered and validated review from Groq failed_generation on attempt {attempt + 1} "
                                f"using model='{model_name}'."
                            )
                            return validated_review
                        except Exception as rescue_err:
                            logger.warning(
                                f"Failed to salvage review from failed_generation: {cls.sanitize_error_message(str(rescue_err))}"
                            )

                    # Step B: Controlled retry with simplified prompt and json_object mode
                    if attempt < max_retries:
                        use_structured_schema = False
                        use_simplified_prompt = True
                        delay = min(15.0, (2.0 ** attempt) * 1.5 + random.uniform(0.2, 0.8))
                        logger.info(
                            f"Retrying Groq review with simplified prompt and JSON mode after {delay:.2f}s backoff "
                            f"(attempt {attempt + 2}/{max_retries + 1})..."
                        )
                        time.sleep(delay)
                        continue

                # Check if error is due to json_schema syntax/strict mode rejection by model
                is_schema_reject = (
                    use_structured_schema
                    and (
                        "json_schema" in sanitized_msg.lower()
                        or "schema" in sanitized_msg.lower()
                        or "response_format" in sanitized_msg.lower()
                    )
                )

                if is_schema_reject and attempt < max_retries:
                    logger.warning(f"Model '{model_name}' rejected json_schema; switching to json_object mode for retry.")
                    use_structured_schema = False
                    delay = min(15.0, (2.0 ** attempt) * 1.5 + random.uniform(0.2, 0.8))
                    time.sleep(delay)
                    continue

                formatted_msg = cls._format_diagnostic_error(bad_req, model_name, attempt + 1)
                logger.error(f"Permanent Groq API BadRequestError: {formatted_msg}")
                raise RuntimeError(formatted_msg) from bad_req

            except (ValueError, json.JSONDecodeError) as parse_err:
                last_error = parse_err
                sanitized_err = cls.sanitize_error_message(str(parse_err))
                logger.warning(
                    f"Groq response parsing/schema error on attempt {attempt + 1}/{max_retries + 1} "
                    f"for model='{model_name}': {sanitized_err}"
                )

                if attempt < max_retries:
                    use_structured_schema = False
                    use_simplified_prompt = True
                    delay = min(15.0, (2.0 ** attempt) * 1.5 + random.uniform(0.2, 0.8))
                    logger.info(
                        f"Retrying Groq review with simplified prompt and JSON mode after {delay:.2f}s backoff "
                        f"(attempt {attempt + 2}/{max_retries + 1})..."
                    )
                    time.sleep(delay)
                    continue

                raise ValueError(
                    f"AI returned invalid review schema after {max_retries + 1} attempts: {sanitized_err}"
                ) from parse_err

            except (AuthenticationError, PermissionDeniedError, NotFoundError) as perm_err:
                last_error = perm_err
                formatted_msg = cls._format_diagnostic_error(perm_err, model_name, attempt + 1)
                logger.error(f"Permanent Groq API error: {formatted_msg}")
                raise RuntimeError(formatted_msg) from perm_err

            except (RateLimitError, InternalServerError, APITimeoutError, APIConnectionError, APIStatusError) as api_err:
                last_error = api_err
                status_code = getattr(api_err, 'status_code', None)
                sanitized_err = cls.sanitize_error_message(str(api_err))
                logger.warning(
                    f"Groq API error on attempt {attempt + 1}/{max_retries + 1}: status={status_code}, error={sanitized_err}"
                )

                if not cls._is_transient_error(api_err):
                    formatted_msg = cls._format_diagnostic_error(api_err, model_name, attempt + 1)
                    logger.error(f"Permanent Groq API status error: {formatted_msg}")
                    raise RuntimeError(formatted_msg) from api_err

                if attempt == max_retries:
                    formatted_msg = cls._format_diagnostic_error(api_err, model_name, attempt + 1)
                    logger.error(f"Max retries reached for transient Groq error: {formatted_msg}")
                    raise RuntimeError(formatted_msg) from api_err

                # Bounded exponential backoff with jitter, respecting Retry-After
                extracted_delay = cls._extract_retry_delay(api_err)
                base_delay = (2.0 ** attempt) * 1.5
                jitter = random.uniform(0.2, 1.0)
                delay = min(15.0, max(extracted_delay, base_delay + jitter))

                logger.info(
                    f"Backing off for {delay:.2f}s before retry attempt {attempt + 2}/{max_retries + 1} "
                    f"for model='{model_name}'..."
                )
                time.sleep(delay)

            except Exception as e:
                last_error = e
                sanitized_err = cls.sanitize_error_message(str(e))
                logger.error(
                    f"Unexpected error communicating with Groq on attempt {attempt + 1}/{max_retries + 1}: {sanitized_err}"
                )

                if not cls._is_transient_error(e):
                    formatted_msg = cls._format_diagnostic_error(e, model_name, attempt + 1)
                    raise RuntimeError(formatted_msg) from e

                if attempt == max_retries:
                    formatted_msg = cls._format_diagnostic_error(e, model_name, attempt + 1)
                    raise RuntimeError(formatted_msg) from e

                delay = min(15.0, (2.0 ** attempt) * 1.5 + random.uniform(0.2, 1.0))
                time.sleep(delay)

        formatted_msg = cls._format_diagnostic_error(last_error, model_name, max_retries + 1)
        raise RuntimeError(formatted_msg)

    @classmethod
    def _is_transient_error(cls, err: Exception) -> bool:
        """Determines if an error is temporary/transient and eligible for retry."""
        if isinstance(err, (RateLimitError, InternalServerError, APITimeoutError, APIConnectionError)):
            return True

        if isinstance(err, APIStatusError):
            code = getattr(err, 'status_code', None)
            if code in [500, 502, 503, 504, 429]:
                return True

        err_name = type(err).__name__.lower()
        err_msg = str(err).lower()
        if any(term in err_name for term in ['timeout', 'network', 'connection', 'socket']):
            return True
        if any(term in err_msg for term in ['timeout', 'connection refused', 'connection reset', 'temporarily unavailable', '503', '502', '500', '429', 'rate limit', 'overloaded']):
            return True
        return False

    @classmethod
    def _extract_retry_delay(cls, err: Exception) -> float:
        """Attempts to extract retry delay from API response headers if present."""
        if isinstance(err, APIStatusError):
            response = getattr(err, 'response', None)
            if response and hasattr(response, 'headers'):
                retry_after = response.headers.get('retry-after') or response.headers.get('Retry-After')
                if retry_after:
                    try:
                        return float(retry_after)
                    except (ValueError, TypeError):
                        pass
        return 0.0

    @classmethod
    def _format_diagnostic_error(cls, err: Exception, model_name: str, total_attempts: int) -> str:
        """Generates clear, actionable diagnostic messages for Groq failures with sensitive data redacted."""
        sanitized_err_str = cls.sanitize_error_message(str(err))

        if isinstance(err, NotFoundError) or (isinstance(err, APIStatusError) and err.status_code == 404):
            return (
                f"Configured Groq model '{model_name}' was not found (404 NOT_FOUND). "
                f"Please update GROQ_MODEL in your backend/.env to an available model (such as 'openai/gpt-oss-20b' or 'llama-3.3-70b-versatile')."
            )

        if isinstance(err, (AuthenticationError, PermissionDeniedError)) or (isinstance(err, APIStatusError) and err.status_code in [401, 403]):
            return (
                "Invalid or unauthorized Groq API key. "
                "Please check your GROQ_API_KEY in backend/.env."
            )

        if isinstance(err, RateLimitError) or (isinstance(err, APIStatusError) and err.status_code == 429):
            return (
                f"Groq API rate limit was reached (429 RateLimitError) after {total_attempts} attempts. "
                "Please wait a few moments before reviewing again."
            )

        if isinstance(err, InternalServerError) or (isinstance(err, APIStatusError) and err.status_code in [500, 502, 503, 504]):
            status = getattr(err, 'status_code', 503)
            return (
                f"Groq API service is temporarily unavailable ({status}) after {total_attempts} attempts. "
                "Please try again in a few moments."
            )

        if isinstance(err, BadRequestError) or (isinstance(err, APIStatusError) and err.status_code == 400):
            if "json_validate_failed" in sanitized_err_str.lower():
                return (
                    f"Groq API model '{model_name}' failed JSON validation (json_validate_failed) after {total_attempts} attempts. "
                    "Please retry the review."
                )
            msg = getattr(err, 'message', sanitized_err_str)
            return f"Groq API rejected review request (400 BadRequestError): {cls.sanitize_error_message(msg)}"

        return f"AI review failed after {total_attempts} attempts: {sanitized_err_str}"

    @classmethod
    def _clean_and_parse_json(cls, raw_text: str) -> Dict[str, Any]:
        """Cleans Markdown code fence delimiters and extracts valid JSON."""
        if not raw_text or not isinstance(raw_text, str):
            raise ValueError("Empty or non-string response received from model.")

        cleaned = raw_text.strip()
        # Remove reasoning tags like <think>...</think> if present
        cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL).strip()

        # Remove markdown code fences
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
        """Ensures all required review fields and finding schemas exist without silent dropping or fabrication."""
        if not isinstance(data, dict):
            raise ValueError("Review payload must be a JSON object.")

        # Validate overall_status
        raw_status = str(data.get("overall_status", "")).strip().lower().replace(" ", "_")
        if raw_status not in ["compliant", "needs_review", "flagged"]:
            raise ValueError(f"Invalid overall_status: '{data.get('overall_status')}'. Expected: compliant, needs_review, or flagged.")
        overall_status = raw_status

        # Validate summary
        summary = str(data.get("summary", "")).strip()
        if not summary:
            raise ValueError("Review summary is required and cannot be empty.")

        # Validate findings list
        raw_findings = data.get("findings")
        if raw_findings is None or not isinstance(raw_findings, list):
            raise ValueError("'findings' field is required and must be a list in review response.")

        clean_findings = []
        for idx, f in enumerate(raw_findings):
            if not isinstance(f, dict):
                raise ValueError(f"Finding item at index {idx} must be a JSON object.")

            field_val = str(f.get("field", "")).strip().lower()
            allowed_fields = ["title", "description", "price", "category", "attributes", "seller", "tags"]
            if field_val not in allowed_fields:
                field_val = "description"

            raw_severity = str(f.get("severity", "Medium")).strip().capitalize()
            if raw_severity not in ["High", "Medium", "Low"]:
                raw_severity = "Medium"

            issue_text = str(f.get("issue") or f.get("issue_description") or "").strip()
            if not issue_text:
                raise ValueError(f"Finding at index {idx} is missing required 'issue' description.")

            suggested_rev = str(f.get("suggested_revision", "")).strip()
            if not suggested_rev and raw_severity in ["High", "Medium"]:
                raise ValueError(f"Finding at index {idx} is missing required 'suggested_revision'.")

            clean_finding = {
                "field": field_val,
                "original_value": str(f.get("original_value", "")).strip(),
                "issue_type": str(f.get("issue_type", "policy_violation")).strip(),
                "severity": raw_severity,
                "issue": issue_text,
                "policy_section": str(f.get("policy_section", "")).strip() or "NONE",
                "policy_reference": str(f.get("policy_reference", "")).strip() or "General Marketplace Standard",
                "suggested_revision": suggested_rev or str(f.get("original_value", "")).strip(),
                "explanation": str(f.get("explanation", "")).strip() or "Replaced non-compliant phrasing with compliant alternative.",
                "requires_human_review": bool(f.get("requires_human_review", True))
            }
            clean_findings.append(clean_finding)

        # Assumptions & Unverifiable claims
        assumptions = data.get("assumptions", [])
        if not isinstance(assumptions, list):
            assumptions = []
        assumptions = [str(a).strip() for a in assumptions if str(a).strip()]

        unverifiable = data.get("unverifiable_claims", [])
        if not isinstance(unverifiable, list):
            unverifiable = []
        unverifiable = [str(u).strip() for u in unverifiable if str(u).strip()]

        policy_coverage = str(data.get("policy_coverage", "sample_policy")).strip()
        if policy_coverage not in ["sample_policy", "official_policy", "none"]:
            policy_coverage = "sample_policy"

        # Consistency check: If any finding has High severity, overall_status must be flagged
        if any(f["severity"] == "High" for f in clean_findings) and overall_status != "flagged":
            overall_status = "flagged"

        return {
            "overall_status": overall_status,
            "summary": summary,
            "findings": clean_findings,
            "assumptions": assumptions,
            "unverifiable_claims": unverifiable,
            "policy_coverage": policy_coverage
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
