from datetime import datetime
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
import jwt
import requests as http_requests
from ..schemas.billing import Plan, PlanFeature, PlansResponse, SubscriptionResponse, SubscriptionRequest, UserManagementSubscriptionRequest

router = APIRouter(prefix="/billing-manager", tags=["Billing"])

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://192.168.68.111:8002/user")

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secret_key')
ALGORITHM = "HS256"

def get_current_user(token: str = Header(None)):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
    
SUBSCRIPTION_PLANS = [
    Plan(
        id="67c52598-c06c-4e38-a5a3-d7c647cfa0dc",
        name="Emprendedor",
        price=99.00,
        features=[
            PlanFeature(description="Registro de PQRs"),
            PlanFeature(description="Atención telefónica"),
            PlanFeature(description="Escalamiento automatizado"),
            PlanFeature(description="Reportes básicos")
        ]
    ),
    Plan(
        id="2e3f1f37-3048-4c71-a28f-b8e8c1332c4e", 
        name="Empresario",
        price=199.00,
        features=[
            PlanFeature(description="Todo de Emprendedor"),
            PlanFeature(description="Soporte multicanal"),
            PlanFeature(description="Llamadas salientes"),
            PlanFeature(description="Panel de control avanzado")
        ]
    ),
    Plan(
        id="9d3f6f4b-6d9a-4f1f-9c9f-1c9f1c9f1c9f",
        name="Empresario Plus",
        price=299.00,
        features=[
            PlanFeature(description="Todas de Empresario"),
            PlanFeature(description="Análisis con IA"),
            PlanFeature(description="Modelos predictivos"),
            PlanFeature(description="Soporte con IA generativa")
        ]
    )
]

def link_subscription_to_user(subscription_data: UserManagementSubscriptionRequest, token: str):
    api_url = USER_SERVICE_URL
    endpoint = "/company/assign-plan" 
    headers = {
        "token": f"{token}",
        "Content-Type": "application/json"
    }
    
    data = subscription_data.model_dump_json()
    
    try:
        response = http_requests.post(f"{api_url}{endpoint}", headers=headers, data=data)
        return response.json(), response.status_code
    except http_requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to user management service: {str(e)}"}, 500

@router.get("/plans", response_model=PlansResponse)
async def get_subscription_plans(
    current_user: dict = Depends(get_current_user)
):   
    if not current_user:
       raise HTTPException(status_code=401, detail="Authentication required")
    
    if current_user['user_type'] not in ['company']:
       raise HTTPException(status_code=403, detail="Not authorized to view users")
    
    return PlansResponse(plans=SUBSCRIPTION_PLANS)

@router.post("/assign-plan", response_model=SubscriptionResponse)
async def subscribe_to_plan(subscription: SubscriptionRequest,
        current_user: dict = Depends(get_current_user)                     
    ):
    
    if not current_user:
       raise HTTPException(status_code=401, detail="Authentication required")
    
    if current_user['user_type'] not in ['company']:
       raise HTTPException(status_code=403, detail="Not authorized to view users")
    
    token = jwt.encode(current_user, SECRET_KEY, algorithm=ALGORITHM)

    plan = next((p for p in SUBSCRIPTION_PLANS if p.id == subscription.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    user_management_subscription = UserManagementSubscriptionRequest(
        plan_id=subscription.plan_id,
        company_id=subscription.company_id
    )
    
    response_data, status_code = link_subscription_to_user(user_management_subscription, token)
    if status_code != 200:
        raise HTTPException(
            status_code=status_code,
            detail=response_data.get("detail", "Failed to link subscription to user")
        )
    
    subscription_id = str(uuid.uuid4())
    
    return SubscriptionResponse(
        subscription_id=subscription_id,
        status="active",
        message="Subscription created successfully",
        plan_id=subscription.plan_id,
        company_id=subscription.company_id
    )