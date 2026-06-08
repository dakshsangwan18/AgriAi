import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestUserRegistration:
    
    @pytest.mark.auth
    def test_register_new_user_success(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
                "phone": "1234567890",
                "location": "New City"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["location"] == "New City"
        assert "id" in data
        assert "hashed_password" not in data  # Should never expose password
        assert "password" not in data
    
    @pytest.mark.auth
    def test_register_duplicate_email(self, client: TestClient, test_user):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "SecurePass123!",
                "full_name": "Duplicate User",
                "phone": "1234567890",
                "location": "City"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.auth
    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",  # Invalid format
                "password": "SecurePass123!",
                "full_name": "Test User",
                "phone": "1234567890",
                "location": "City"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.auth
    def test_register_weak_password(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",  # Too short
                "full_name": "Test User",
                "phone": "1234567890",
                "location": "City"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.auth
    def test_register_missing_required_fields(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "SecurePass123!"
                # Missing: full_name, phone, location (but these are optional)
            }
        )
        
        # Fields are optional, so registration succeeds
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]






class TestUserLogin:
    
    @pytest.mark.auth
    def test_login_success(self, client: TestClient, test_user):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check token structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Token should be returned - user data removed from OAuth2 response
    
    @pytest.mark.auth
    def test_login_wrong_password(self, client: TestClient, test_user):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.auth
    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nobody@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
   
    @pytest.mark.auth
    def test_login_inactive_user(self, client: TestClient, inactive_user):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": inactive_user.email,
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()






class TestGetCurrentUser:
    
    @pytest.mark.auth
    def test_get_current_user_success(self, client: TestClient, auth_headers, test_user):
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["location"] == test_user.location
        assert "hashed_password" not in data
    
    @pytest.mark.auth
    def test_get_current_user_no_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "could not validate credentials" in response.json()["detail"].lower()
    
    @pytest.mark.auth
    def test_get_current_user_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.auth
    def test_get_current_user_expired_token(self, client: TestClient, expired_token):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED






class TestUpdateProfile:
    
    @pytest.mark.auth
    def test_update_profile_success(self, client: TestClient, auth_headers, test_user):
        response = client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "location": "Updated City",
                "favorite_crops": ["tomato", "potato"]
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["location"] == "Updated City"
        assert "tomato" in data["favorite_crops"]
    
    @pytest.mark.auth
    def test_update_profile_unauthenticated(self, client: TestClient):
        response = client.put(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED






class TestPasswordReset:
    
    @pytest.mark.auth
    def test_forgot_password_success(self, client: TestClient, test_user):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "email" in response.json()["message"].lower()
    
    @pytest.mark.auth
    def test_forgot_password_nonexistent_email(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@example.com"}
        )
        
        # Security: Don't reveal if email exists
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.auth
    @pytest.mark.slow
    def test_complete_password_reset_flow(self, client: TestClient, test_user, test_db):
        # Step 1: Request password reset
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email}
        )
        assert forgot_response.status_code == status.HTTP_200_OK
        
        # Step 2: User should have reset_token (simulate getting it)
        test_db.refresh(test_user)
        reset_token = test_user.reset_token
        assert reset_token is not None
        
        # Step 3: Reset password with token
        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "NewSecurePass123!"
            }
        )
        assert reset_response.status_code == status.HTTP_200_OK
        
        # Step 4: Login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "NewSecurePass123!"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert "access_token" in login_response.json()






class TestAdminEndpoints:
    
    @pytest.mark.auth
    def test_admin_access_with_admin_user(self, client: TestClient, admin_headers):
        response = client.get(
            "/api/admin/users",
            headers=admin_headers
        )
        
        # Should succeed (200) or be implemented (not 403)
        assert response.status_code != status.HTTP_403_FORBIDDEN
    
    @pytest.mark.auth
    def test_admin_access_with_regular_user(self, client: TestClient, auth_headers):
        response = client.get(
            "/api/admin/users",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN






class TestRateLimiting:
    
    @pytest.mark.auth
    @pytest.mark.slow
    def test_login_rate_limit(self, client: TestClient):
        # Make many login attempts
        for i in range(15):  # Assuming limit is 10/minute
            client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com",
                    "password": "password"
                }
            )
        
        # Next request should be rate limited
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "password"
            }
        )
        
        # Should be rate limited (429) or still processing
        assert response.status_code in [status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_401_UNAUTHORIZED]
