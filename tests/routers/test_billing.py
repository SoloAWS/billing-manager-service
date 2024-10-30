import os
from unittest.mock import patch, MagicMock
import pytest
import jwt
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.billing import SubscriptionRequest, SubscriptionResponse, UserManagementSubscriptionRequest

client = TestClient(app)

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secret_key')
ALGORITHM = "HS256"

@pytest.fixture
def test_token():
    token_data = {
        "sub": str(uuid4()),
        "user_type": "company"
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

@pytest.fixture
def mock_link_subscription():
    with patch('app.routers.billing.link_subscription_to_user') as mock:
        yield mock

@pytest.fixture
def mock_get_current_user():
    with patch('app.routers.billing.get_current_user') as mock:
        mock.return_value = {'sub': 'test_user', 'user_type': 'company'}
        yield mock

def test_get_plans_success(test_token):
    response = client.get(
        "/billing-manager/plans",
        headers={"Authorization": test_token}
    )
    
    assert response.status_code == 200
    assert "plans" in response.json()
    assert len(response.json()["plans"]) == 3
    
    plans = response.json()["plans"]
    assert plans[0]["name"] == "Emprendedor"
    assert plans[1]["name"] == "Empresario"
    assert plans[2]["name"] == "Empresario Plus"

def test_subscribe_to_plan_success(test_token, mock_link_subscription):
    mock_link_subscription.return_value = ({"message": "Plan assigned successfully"}, 200)
    
    request_data = {
        "plan_id": "67c52598-c06c-4e38-a5a3-d7c647cfa0dc",
        "company_id": str(uuid4()),
        "card_info": {
            "card_number": "4532015112830366",
            "expiration_date": "12/25",
            "cvv": "123",
            "card_holder_name": "John Doe"
        }
    }

    response = client.post(
        "/billing-manager/assign-plan",
        json=request_data,
        headers={"Authorization": test_token}
    )

    assert response.status_code == 200
    assert "subscription_id" in response.json()
    assert response.json()["status"] == "active"
    assert response.json()["plan_id"] == request_data["plan_id"]
    assert response.json()["company_id"] == request_data["company_id"]

def test_subscribe_to_plan_invalid_plan_id(test_token):
    request_data = {
        "plan_id": "invalid-plan-id",
        "company_id": str(uuid4()),
        "card_info": {
            "card_number": "4532015112830366",
            "expiration_date": "12/25",
            "cvv": "123",
            "card_holder_name": "John Doe"
        }
    }

    response = client.post(
        "/billing-manager/assign-plan",
        json=request_data,
        headers={"Authorization": test_token}
    )

    assert response.status_code == 404
    assert "detail" in response.json()
    assert response.json()["detail"] == "Plan not found"

def test_subscribe_to_plan_invalid_card_number(test_token):
    request_data = {
        "plan_id": "67c52598-c06c-4e38-a5a3-d7c647cfa0dc",
        "company_id": str(uuid4()),
        "card_info": {
            "card_number": "invalid",
            "expiration_date": "12/25",
            "cvv": "123",
            "card_holder_name": "John Doe"
        }
    }

    response = client.post(
        "/billing-manager/assign-plan",
        json=request_data,
        headers={"Authorization": test_token}
    )

    assert response.status_code == 400

def test_subscribe_to_plan_user_management_error(test_token, mock_link_subscription):
    mock_link_subscription.return_value = ({"detail": "Error assigning plan"}, 500)
    
    request_data = {
        "plan_id": "67c52598-c06c-4e38-a5a3-d7c647cfa0dc",
        "company_id": str(uuid4()),
        "card_info": {
            "card_number": "4532015112830366",
            "expiration_date": "12/25",
            "cvv": "123",
            "card_holder_name": "John Doe"
        }
    }

    response = client.post(
        "/billing-manager/assign-plan",
        json=request_data,
        headers={"Authorization": test_token}
    )

    assert response.status_code == 500
    assert "detail" in response.json()

def test_link_subscription_to_user_success():
    with patch('app.routers.billing.http_requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": "Success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        subscription_data = UserManagementSubscriptionRequest(
            plan_id="67c52598-c06c-4e38-a5a3-d7c647cfa0dc",
            company_id=str(uuid4())
        )

        from app.routers.billing import link_subscription_to_user
        response_data, status_code = link_subscription_to_user(subscription_data, "test-token")

        assert status_code == 200
        assert response_data == {"message": "Success"}
        mock_post.assert_called_once()

def test_get_current_user_valid_token():
    with patch('app.routers.billing.jwt.decode') as mock_decode:
        mock_decode.return_value = {'sub': 'test_user', 'user_type': 'company'}
        from app.routers.billing import get_current_user
        user = get_current_user('valid_token')
        assert user == {'sub': 'test_user', 'user_type': 'company'}

def test_get_current_user_invalid_token():
    from app.routers.billing import get_current_user
    user = get_current_user('invalid_token')
    assert user is None

def test_get_current_user_no_token():
    from app.routers.billing import get_current_user
    user = get_current_user(None)
    assert user is None