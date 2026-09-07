import pytest
import io
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt import get_current_user
from app.services.lead_verifier import LeadVerificationEngine, VERIFICATION_ACCEPTANCE_THRESHOLD
from app.services.lead_importer import LeadDatasetImporter

client = TestClient(app)

ADMIN_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": "admin@euroshub.test",
    "name": "Admin Test User",
    "role": "admin",
}

EMPLOYEE_USER = {
    "id": "22222222-2222-2222-2222-222222222222",
    "email": "employee@euroshub.test",
    "name": "Employee Test User",
    "role": "employee",
}


@pytest.fixture(autouse=True)
def cleanup_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


# ==============================================================================
# 1. SYSTEM & HEALTH CHECKS
# ==============================================================================

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data


def test_root_check():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


# ==============================================================================
# 2. AUTHENTICATION & AUTHORIZATION TESTS
# ==============================================================================

def test_unauthenticated_requests_rejected():
    res = client.get("/auth/me")
    assert res.status_code == 401
    assert "detail" in res.json() or "message" in res.json()


def test_authenticated_me_as_employee():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    res = client.get("/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == EMPLOYEE_USER["id"]
    assert data["role"] == "employee"


def test_employee_can_list_users_for_assignment():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    res = client.get("/auth/users")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_employee_cannot_create_users():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    res = client.post("/auth/users", json={
        "name": "Forbidden User",
        "email": "forbidden@euroshub.test",
        "role": "employee"
    })
    assert res.status_code == 403


def test_admin_can_list_users():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    res = client.get("/auth/users")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_employee_cannot_create_teams():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    res = client.post("/teams", json={"name": "Forbidden Team", "description": "Should fail"})
    assert res.status_code == 403


def test_admin_can_manage_teams():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    # List teams
    res = client.get("/teams")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Create team with unique name
    unique_team_name = f"QA Alpha Team {uuid.uuid4().hex[:6]}"
    res = client.post("/teams", json={"name": unique_team_name, "description": "Automated test team"})
    assert res.status_code in (200, 201)
    team = res.json()
    team_id = team["id"]

    # Read team
    res = client.get(f"/teams/{team_id}")
    assert res.status_code == 200
    assert res.json()["name"] == unique_team_name


# ==============================================================================
# 3. LEADS CRUD & PIPELINE TESTS
# ==============================================================================

def test_leads_crud_flow():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER

    # Create lead
    lead_payload = {
        "company_name": "Test Acme Enterprise",
        "contact_name": "John Doe",
        "email": "john.doe@testacme.com",
        "phone": "+1-555-123-4567",
        "website": "https://testacme.com",
        "status": "NEW",
        "priority": "HIGH",
        "source": "Upwork",
    }
    res = client.post("/leads", json=lead_payload)
    assert res.status_code in (200, 201)
    created = res.json()
    lead_id = created["id"]
    assert created["company_name"] == "Test Acme Enterprise"

    # Read lead
    res = client.get(f"/leads/{lead_id}")
    assert res.status_code == 200
    assert res.json()["id"] == lead_id

    # Update lead
    res = client.put(f"/leads/{lead_id}", json={"status": "QUALIFIED", "budget": 25000})
    assert res.status_code == 200
    assert res.json()["status"] == "QUALIFIED"

    # List leads
    res = client.get("/leads")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(l["id"] == lead_id for l in data)


def test_duplicate_checker():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    # Check duplicate on non-existent
    res = client.post("/leads/check-duplicates", json={
        "company_name": "Definitely Unique Co",
        "email": "unique.never.seen@domain.com"
    })
    assert res.status_code == 200
    data = res.json()
    assert "has_duplicate" in data


# ==============================================================================
# 4. VERIFICATION ENGINE UNIT TESTS
# ==============================================================================

def test_lead_verifier_scoring_rules():
    # Complete high quality lead
    res = LeadVerificationEngine.verify_lead({
        "company_name": "Valid Enterprise Inc",
        "email": "contact@google.com",
        "phone": "+1 415 555 2671",
        "website": "https://google.com",
        "contact_name": "Sergey Brin",
        "job_title": "Co-Founder",
        "country": "United States",
        "industry": "Technology",
    })
    assert res["verification_score"] >= VERIFICATION_ACCEPTANCE_THRESHOLD
    assert res["verification_status"] == "VERIFIED"

    # Poor quality lead with invalid email and blocked host
    res_low = LeadVerificationEngine.verify_lead({
        "company_name": "",
        "email": "notanemail",
        "phone": "123",
        "website": "http://127.0.0.1",
        "contact_name": "",
        "job_title": "",
        "country": "",
        "industry": "",
    })
    assert res_low["verification_score"] < VERIFICATION_ACCEPTANCE_THRESHOLD
    assert res_low["verification_status"] == "REJECTED"


# ==============================================================================
# 5. DATASET IMPORT PREVIEW & PROCESSING TESTS
# ==============================================================================

def test_dataset_preview():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    csv_content = (
        "Company,Contact Name,Job Title,Email,Website,Country\n"
        "Beta Cloud,Alice Smith,CTO,alice@betacloud.io,https://betacloud.io,USA\n"
        "Delta Tech,Bob Ray,VP,bob@deltatech.co,https://deltatech.co,UK\n"
    )
    files = {"file": ("leads.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post("/leads/import/preview", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "detected_headers" in data
    assert "preview_rows" in data
    assert len(data["preview_rows"]) == 2
    assert "company_name" in data["suggested_mappings"].values()


def test_dataset_preview_empty_file():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    res = client.post("/leads/import/preview", files=files)
    assert res.status_code in (400, 422)


def test_dataset_preview_unsupported_extension():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    files = {"file": ("malicious.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    res = client.post("/leads/import/preview", files=files)
    assert res.status_code in (400, 422)


# ==============================================================================
# 6. ACTIVITIES & TASKS TESTS
# ==============================================================================

def test_activities_and_tasks_flow():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER

    # Create lead to attach activity & task to
    lead_res = client.post("/leads", json={"company_name": "Task Test Corp"})
    assert lead_res.status_code in (200, 201)
    lead_id = lead_res.json()["id"]

    # Log activity
    act_res = client.post(
        f"/leads/{lead_id}/activities",
        json={
            "type": "Phone Call",
            "title": "Initial discovery call",
            "summary": "Initial discovery call",
            "description": "Client expressed interest in Q4 redesign project",
        }
    )
    assert act_res.status_code in (200, 201)

    # List activities
    act_list = client.get(f"/leads/{lead_id}/activities")
    assert act_list.status_code == 200
    assert len(act_list.json()) >= 1

    # Create task
    task_res = client.post(
        "/tasks",
        json={
            "lead_id": lead_id,
            "title": "Send proposal draft",
            "status": "PENDING",
            "priority": "HIGH",
        }
    )
    assert task_res.status_code in (200, 201)
    task_id = task_res.json()["id"]

    # Update task
    update_res = client.put(f"/tasks/{task_id}", json={"status": "COMPLETED"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "COMPLETED"


# ==============================================================================
# 7. DASHBOARD & SETTINGS
# ==============================================================================

def test_dashboard_stats():
    app.dependency_overrides[get_current_user] = lambda: EMPLOYEE_USER
    res = client.get("/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_leads" in stats
    assert "total_pipeline_value" in stats
    assert "leads_by_status" in stats


def test_settings_flow():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    res = client.get("/settings/system")
    assert res.status_code == 200
    data = res.json()
    assert "project_name" in data
    assert "environment" in data

    res_sources = client.get("/settings/sources")
    assert res_sources.status_code == 200
    assert isinstance(res_sources.json(), list)
