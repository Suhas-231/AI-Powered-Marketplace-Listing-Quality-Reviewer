import json
import httpx
from unittest.mock import patch, MagicMock
import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.listing import Listing
from app.models.policy import Policy
from app.models.user import User
from app.services.groq_service import GroqService
from groq import AuthenticationError, NotFoundError, RateLimitError, InternalServerError, BadRequestError

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = User(name="Review Tester", email="rev@test.local", role="reviewer")
        db.session.add(user)

        # Seed policy
        p = Policy(
            policy_code="POL-HLTH-001",
            section_number="Section 4.1",
            title="Disease Cure Claims",
            category="Medical and health claims",
            description="Non-certified products must never claim to cure diseases.",
            severity_guidance="High",
            is_active=True,
            is_demo_policy=True
        )
        db.session.add(p)

        # Seed listing
        listing = Listing(
            title="Miracle Herbal Cure Diabetes",
            description="Herbal remedy to cure diabetes and cancer naturally.",
            category="Health & Personal Care",
            price=39.99,
            seller="Vitality"
        )
        db.session.add(listing)
        db.session.commit()

        yield app.test_client()
        db.drop_all()

def test_trigger_ai_review_mock(client):
    # Trigger review using default mock handler in TestingConfig
    res = client.post('/api/listings/1/review')
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    review = data['review']
    assert review['status'] == 'completed'
    assert len(review['findings']) > 0
    assert review['policy_coverage'] == 'sample_policy'

    # Check listing status changed to revisions_pending
    l_res = client.get('/api/listings/1')
    assert l_res.get_json()['status'] == 'revisions_pending'

def test_review_validation_failure_prevents_ai_review(client):
    # Create invalid listing directly
    invalid_listing = Listing(
        title="Bad",  # Too short
        description="Short",
        category="Health & Personal Care",
        price=10.0,
        seller="Seller"
    )
    with client.application.app_context():
        db.session.add(invalid_listing)
        db.session.commit()
        inv_id = invalid_listing.id

    # Attempt to trigger review on invalid listing
    res = client.post(f'/api/listings/{inv_id}/review')
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'validation_errors' in data

def test_delete_ai_review(client):
    # Trigger review first
    res = client.post('/api/listings/1/review')
    assert res.status_code == 201
    rev_id = res.get_json()['review']['id']

    # Confirm listing status is revisions_pending
    l_res = client.get('/api/listings/1')
    assert l_res.get_json()['status'] == 'revisions_pending'

    # Check reviews list
    rev_list = client.get('/api/reviews')
    assert rev_list.status_code == 200
    assert rev_list.get_json()['total'] == 1

    # Delete review
    del_res = client.delete(f'/api/reviews/{rev_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True

    # Review should no longer exist
    get_res = client.get(f'/api/reviews/{rev_id}')
    assert get_res.status_code == 404

    # Listing status should have reverted to draft
    l_res2 = client.get('/api/listings/1')
    assert l_res2.get_json()['status'] == 'draft'

def test_groq_structured_json_output_success():
    """Tests Groq chat completion returning structured JSON schema output."""
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "overall_status": "flagged",
        "summary": "Compliance violation detected in product title.",
        "findings": [
            {
                "field": "title",
                "original_value": "Miracle Herbal Cure Diabetes",
                "issue_type": "misleading_claim",
                "severity": "High",
                "issue": "Prohibited disease cure claims found in title.",
                "policy_section": "POL-HLTH-001",
                "policy_reference": "Disease Cure Claims",
                "suggested_revision": "Herbal Wellness Tea Blend",
                "explanation": "Removed uncertified medical promises.",
                "requires_human_review": True
            }
        ],
        "assumptions": ["Assumed uncertified supplement."],
        "unverifiable_claims": ["Cure diabetes claim."],
        "policy_coverage": "sample_policy"
    })

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client):
            result = GroqService.analyze_listing(
                {'title': 'Miracle Herbal Cure Diabetes', 'description': 'Herbal tea description'},
                'POL-HLTH-001'
            )
            assert result['overall_status'] == 'flagged'
            assert len(result['findings']) == 1
            assert result['findings'][0]['policy_section'] == 'POL-HLTH-001'
            assert result['findings'][0]['suggested_revision'] == 'Herbal Wellness Tea Blend'
            assert mock_client.chat.completions.create.call_count == 1

def test_groq_json_schema_fallback_to_json_object():
    """Tests fallback to json_object mode when model does not support strict json_schema."""
    req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
    bad_req_err = BadRequestError(
        "Model 'openai/gpt-oss-20b' does not support response_format json_schema",
        response=httpx.Response(400, request=req),
        body=None
    )

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "overall_status": "compliant",
        "summary": "Parsed via json_object fallback.",
        "findings": [],
        "assumptions": [],
        "unverifiable_claims": [],
        "policy_coverage": "sample_policy"
    })
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    # First call with json_schema fails with 400, second call with json_object succeeds
    mock_client.chat.completions.create.side_effect = [bad_req_err, mock_completion]

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client):
            result = GroqService.analyze_listing({'title': 'Valid Title', 'description': 'Valid Description'}, 'Policies')
            assert result['overall_status'] == 'compliant'
            assert result['summary'] == 'Parsed via json_object fallback.'
            assert mock_client.chat.completions.create.call_count == 2

def test_scenario_b_repeated_reviews_generate_separate_results_and_prevent_stale_data(client):
    # Review 1
    res1 = client.post('/api/listings/1/review')
    assert res1.status_code == 201
    rev1 = res1.get_json()['review']

    # Custom second review with different findings
    different_analysis = {
        "overall_status": "compliant",
        "summary": "Second review: Content revised and compliant.",
        "findings": [],
        "assumptions": [],
        "unverifiable_claims": [],
        "policy_coverage": "sample_policy"
    }

    with patch('app.routes.reviews.GroqService.analyze_listing', return_value=different_analysis):
        res2 = client.post('/api/listings/1/review')
        assert res2.status_code == 201
        rev2 = res2.get_json()['review']

    # Must be two distinct reviews with unique IDs
    assert rev1['id'] != rev2['id']
    assert rev2['summary'] == "Second review: Content revised and compliant."

    # Both reviews preserved in listing history
    l_res = client.get('/api/listings/1')
    listing_data = l_res.get_json()
    assert listing_data['review_count'] == 2
    assert listing_data['latest_review_id'] == rev2['id']

    # Check reviews list has both
    rev_list = client.get('/api/reviews?listing_id=1')
    assert rev_list.get_json()['total'] == 2

def test_scenario_c_first_review_succeeds_second_fails_503_preserves_first(client):
    # Review 1 succeeds
    res1 = client.post('/api/listings/1/review')
    assert res1.status_code == 201
    rev1 = res1.get_json()['review']

    # Review 2 fails with 503 UNAVAILABLE
    err_503 = RuntimeError("Groq API service is temporarily unavailable (503) after 4 attempts.")
    with patch('app.routes.reviews.GroqService.analyze_listing', side_effect=err_503):
        res2 = client.post('/api/listings/1/review')
        assert res2.status_code == 503
        data2 = res2.get_json()
        assert data2['success'] is False
        assert '503' in data2['message']

    # Ensure previous review was NOT overwritten and is still the latest completed review
    l_res = client.get('/api/listings/1')
    listing = l_res.get_json()
    assert listing['latest_review_id'] == rev1['id']

    # Review 1 is still retrieved intact
    get_rev = client.get(f"/api/reviews/{rev1['id']}")
    assert get_rev.status_code == 200
    assert get_rev.get_json()['id'] == rev1['id']

def test_scenario_d_first_review_succeeds_second_fails_429(client):
    # Review 1 succeeds
    res1 = client.post('/api/listings/1/review')
    assert res1.status_code == 201
    rev1 = res1.get_json()['review']

    # Review 2 fails with 429 RateLimitError
    err_429 = RuntimeError("Groq API rate limit was reached (429 RateLimitError) after 4 attempts.")
    with patch('app.routes.reviews.GroqService.analyze_listing', side_effect=err_429):
        res2 = client.post('/api/listings/1/review')
        assert res2.status_code == 429
        data2 = res2.get_json()
        assert data2['success'] is False
        assert '429' in data2['message']

    # Listing still points to review 1
    l_res = client.get('/api/listings/1')
    assert l_res.get_json()['latest_review_id'] == rev1['id']

def test_scenario_e_retry_succeeds_after_transient_failures():
    """Unit test GroqService retry logic on transient errors."""
    req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
    api_err_503 = InternalServerError(
        'Server temporarily overloaded',
        response=httpx.Response(503, request=req, headers={'Retry-After': '0.1'}),
        body=None
    )

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "overall_status": "compliant",
        "summary": "Review after transient retry succeeded.",
        "findings": [],
        "assumptions": [],
        "unverifiable_claims": [],
        "policy_coverage": "sample_policy"
    })
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    # Fails twice with 503, then succeeds on 3rd attempt
    mock_client.chat.completions.create.side_effect = [api_err_503, api_err_503, mock_completion]

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client), \
             patch('time.sleep') as mock_sleep:
            result = GroqService.analyze_listing({'title': 'Valid Title', 'description': 'Valid Description long enough'}, 'Policies')
            assert result['summary'] == "Review after transient retry succeeded."
            assert mock_client.chat.completions.create.call_count == 3
            assert mock_sleep.call_count == 2

def test_scenario_f_invalid_api_key_fails_fast_without_retrying():
    """Permanent 401 AuthenticationError should fail immediately without retrying."""
    req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
    api_err_401 = AuthenticationError(
        'Invalid API Key',
        response=httpx.Response(401, request=req),
        body=None
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = api_err_401

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client), \
             patch('time.sleep') as mock_sleep:
            with pytest.raises(RuntimeError) as exc_info:
                GroqService.analyze_listing({'title': 'Valid Title', 'description': 'Valid Description'}, 'Policies')
            assert 'Invalid or unauthorized Groq API key' in str(exc_info.value)
            # Should fail on first attempt, 0 sleep calls!
            assert mock_client.chat.completions.create.call_count == 1
            assert mock_sleep.call_count == 0

def test_scenario_f_model_not_found_fails_fast_with_clear_diagnostic():
    """Permanent 404 NotFoundError should fail immediately with clear diagnostic."""
    req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
    api_err_404 = NotFoundError(
        'Model not found',
        response=httpx.Response(404, request=req),
        body=None
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = api_err_404

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client), \
             patch('time.sleep') as mock_sleep:
            with pytest.raises(RuntimeError) as exc_info:
                GroqService.analyze_listing({'title': 'Valid Title', 'description': 'Valid Description'}, 'Policies')
            assert '404 NOT_FOUND' in str(exc_info.value)
            assert 'Please update GROQ_MODEL' in str(exc_info.value)
            assert mock_client.chat.completions.create.call_count == 1
            assert mock_sleep.call_count == 0

def test_groq_json_validate_failed_salvage_from_failed_generation():
    """Tests recovering valid review JSON from Groq's failed_generation field."""
    req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
    salvageable_json_text = json.dumps({
        "overall_status": "flagged",
        "summary": "Rescued from failed generation text.",
        "findings": [
            {
                "field": "title",
                "original_value": "Miracle Cure",
                "issue_type": "misleading_claim",
                "severity": "High",
                "issue": "Prohibited disease claims",
                "policy_section": "POL-HLTH-001",
                "policy_reference": "Disease Cure Claims",
                "suggested_revision": "Herbal Tea",
                "explanation": "Removed cure claim",
                "requires_human_review": True
            }
        ],
        "assumptions": [],
        "unverifiable_claims": [],
        "policy_coverage": "sample_policy"
    })
    error_body = {
        "error": {
            "message": "Failed to validate JSON: json_validate_failed",
            "type": "invalid_request_error",
            "code": "json_validate_failed",
            "failed_generation": f"```json\n{salvageable_json_text}\n```"
        }
    }
    json_val_err = BadRequestError(
        "json_validate_failed",
        response=httpx.Response(400, request=req, json=error_body),
        body=error_body
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = json_val_err

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client):
            result = GroqService.analyze_listing({'title': 'Miracle Cure', 'description': 'Herbal tea'}, 'POL-HLTH-001')
            assert result['overall_status'] == 'flagged'
            assert result['summary'] == "Rescued from failed generation text."
            assert len(result['findings']) == 1

def test_groq_json_validate_failed_retries_with_simplified_prompt():
    """Tests that json_validate_failed falls back to simplified prompt and succeeds on retry."""
    req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
    error_body = {
        "error": {
            "message": "Failed to validate JSON: json_validate_failed",
            "type": "invalid_request_error",
            "code": "json_validate_failed",
            "failed_generation": "malformed incomplete output..."
        }
    }
    json_val_err = BadRequestError(
        "json_validate_failed",
        response=httpx.Response(400, request=req, json=error_body),
        body=error_body
    )

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "overall_status": "compliant",
        "summary": "Review succeeded on retry using simplified prompt.",
        "findings": [],
        "assumptions": [],
        "unverifiable_claims": [],
        "policy_coverage": "sample_policy"
    })
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    # 1st call fails with json_validate_failed, 2nd call succeeds with mock_completion
    mock_client.chat.completions.create.side_effect = [json_val_err, mock_completion]

    app = create_app(TestingConfig)
    app.config['GROQ_API_KEY'] = 'unit-test-active-key'
    with app.app_context():
        with patch.object(GroqService, 'get_client', return_value=mock_client), \
             patch('time.sleep') as mock_sleep:
            result = GroqService.analyze_listing({'title': 'Listing 9 Title', 'description': 'Description'}, 'Policies')
            assert result['overall_status'] == 'compliant'
            assert result['summary'] == "Review succeeded on retry using simplified prompt."
            assert mock_client.chat.completions.create.call_count == 2
            assert mock_sleep.call_count == 1

def test_review_listing_with_medical_claims_flags_policy_violations(client):
    """Test a listing containing misleading medical claims generates high severity findings and flagged status."""
    res = client.post('/api/listings/1/review')
    assert res.status_code == 201
    review = res.get_json()['review']
    assert review['overall_status'] == 'flagged'
    findings = review['findings']
    assert len(findings) > 0
    # Must contain high severity disease cure finding
    cure_finding = next((f for f in findings if f['field_name'] == 'title'), None)
    assert cure_finding is not None
    assert cure_finding['severity'] == 'High'
    assert 'POL-HLTH-001' in cure_finding['policy_reference_code']
    assert len(cure_finding['suggested_revision']) > 0

def test_sanitize_error_message_redacts_api_keys():
    """Verify that sensitive Groq API keys and authorization headers are scrubbed from error logs."""
    raw_error = "Failed request with key gsk_AbCdEf1234567890XYZ_test and Bearer tok_sec99214 to https://api.groq.com"
    sanitized = GroqService.sanitize_error_message(raw_error)
    assert 'gsk_' not in sanitized
    assert '[REDACTED_GROQ_KEY]' in sanitized
    assert 'tok_sec99214' not in sanitized
    assert 'Bearer [REDACTED]' in sanitized
