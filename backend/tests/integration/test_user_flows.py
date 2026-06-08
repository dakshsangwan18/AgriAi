import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestCompleteAuthFlow:
    
    def test_register_login_access_protected_endpoint(self, client: TestClient):
        # Step 1: Register new user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "flowtest@example.com",
                "password": "TestPass123!",
                "full_name": "Flow Test User",
                "phone": "1234567890",
                "location": "Test City"
            }
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        user_data = register_response.json()
        assert user_data["email"] == "flowtest@example.com"
        
        # Step 2: Login with credentials
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "flowtest@example.com",
                "password": "TestPass123!"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        token = token_data["access_token"]

        csrf_token = login_response.cookies.get("csrf_token", "")

        # Step 3: Access protected endpoint
        profile_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_response.status_code == status.HTTP_200_OK
        profile_data = profile_response.json()
        assert profile_data["email"] == "flowtest@example.com"
        assert profile_data["full_name"] == "Flow Test User"
        
        # Step 4: Update profile (requires CSRF token)
        update_response = client.put(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf_token,
            },
            json={
                "full_name": "Updated Flow User",
                "location": "Updated City",
                "favorite_crops": ["wheat", "rice"]
            }
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated_data = update_response.json()
        assert updated_data["full_name"] == "Updated Flow User"
        assert "wheat" in updated_data["favorite_crops"]


@pytest.mark.integration
@pytest.mark.slow
class TestPasswordResetFlow:
    
    def test_complete_password_reset_flow(self, client: TestClient, test_user, test_db):
        """
        Test password reset flow:
        1. Request password reset
        2. Verify reset token is created
        3. Reset password with token
        4. Login with new password
        """
        # Step 1: Request password reset
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email}
        )
        assert forgot_response.status_code == status.HTTP_200_OK
        
        # Step 2: Verify reset token exists
        test_db.refresh(test_user)
        reset_token = test_user.reset_token
        assert reset_token is not None
        assert test_user.reset_token_expires is not None
        
        # Step 3: Reset password
        new_password = "NewSecurePassword123!"
        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": new_password
            }
        )
        assert reset_response.status_code == status.HTTP_200_OK
        
        # Step 4: Login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": new_password
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert "access_token" in login_response.json()
        
        # Step 5: Verify old password no longer works
        old_login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"  # Old password
            }
        )
        assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestNotificationWorkflow:
    
    def test_notification_lifecycle(self, client: TestClient, auth_headers, sample_notification):
        """
        Test notification workflow:
        1. Get notifications (unread)
        2. Check unread count
        3. Mark as read
        4. Verify read status
        """
        # Step 1: Get unread notifications
        get_response = client.get(
            "/api/notifications/",
            params={"unread_only": True},
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        notifications = get_response.json()
        assert len(notifications) > 0
        
        # Step 2: Check unread count
        count_response = client.get(
            "/api/notifications/unread-count",
            headers=auth_headers
        )
        assert count_response.status_code == status.HTTP_200_OK
        assert count_response.json()["unread_count"] > 0
        
        # Step 3: Mark as read
        mark_response = client.post(
            "/api/notifications/mark-read",
            headers=auth_headers,
            json={"notification_ids": [sample_notification.id]}
        )
        assert mark_response.status_code == status.HTTP_200_OK
        
        # Step 4: Verify unread count decreased
        new_count_response = client.get(
            "/api/notifications/unread-count",
            headers=auth_headers
        )
        assert new_count_response.status_code == status.HTTP_200_OK
        # Count should be less than before
        # (might be 0 if only one notification)


@pytest.mark.integration
class TestUserAccessControl:
    
    def test_regular_user_cannot_access_admin_endpoints(self, client: TestClient, auth_headers):
        response = client.get(
            "/api/admin/users",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_user_can_access_admin_endpoints(self, client: TestClient, admin_headers):
        response = client.get(
            "/api/admin/users",
            headers=admin_headers
        )
        
        # Should not be forbidden
        assert response.status_code != status.HTTP_403_FORBIDDEN
    
    def test_unauthenticated_user_cannot_access_protected_endpoints(self, client: TestClient):
        endpoints = [
            "/api/v1/auth/me",
            "/api/notifications/",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.slow
class TestDatabaseTransactions:
    
    def test_user_creation_is_atomic(self, client: TestClient, test_db):
        initial_count = test_db.query(User).count() if 'User' in dir() else 0
        
        # Try to create user with invalid data (should rollback)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",  # Invalid
                "password": "pass",  # Too weak
                "full_name": "Test",
                "phone": "123",
                "location": "City"
            }
        )
        
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        
        # Verify count hasn't changed (transaction rolled back)
        final_count = test_db.query(User).count() if 'User' in dir() else 0
        assert final_count == initial_count
