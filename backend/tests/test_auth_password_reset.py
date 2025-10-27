"""
Tests for password reset functionality
Run with: pytest tests/test_auth_password_reset.py -v
Or use VS Code Test Explorer
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.password_reset
class TestPasswordReset:
    """Test password reset flow"""

    async def test_request_password_reset_success(self, client: AsyncClient, registered_user):
        """Test requesting password reset for existing user"""
        email = registered_user["user"]["email"]

        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "If the email exists" in data["message"]

    async def test_request_password_reset_nonexistent_user(self, client: AsyncClient):
        """Test requesting password reset for non-existent user (should not reveal)"""
        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "nonexistent@example.com"}
        )

        # Should return same response to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "If the email exists" in data["message"]

    async def test_request_password_reset_invalid_email(self, client: AsyncClient):
        """Test requesting password reset with invalid email format"""
        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "not-an-email"}
        )

        assert response.status_code == 422  # Validation error

    async def test_verify_valid_token(self, client: AsyncClient, registered_user):
        """Test verifying a valid password reset token"""
        # First, request a password reset
        email = registered_user["user"]["email"]
        await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": email}
        )

        # Note: In a real test, you'd need to extract the token from the email
        # For now, we'll skip the actual token verification test
        # This would require mocking the email service or database access
        pytest.skip("Requires token from email - needs email service mock")

    async def test_verify_invalid_token(self, client: AsyncClient):
        """Test verifying an invalid password reset token"""
        response = await client.post(
            "/api/v1/auth/password-reset/verify",
            json={"token": "invalid-token-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    async def test_reset_password_with_invalid_token(self, client: AsyncClient):
        """Test resetting password with invalid token"""
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "invalid-token-12345",
                "new_password": "NewPassword123"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid or expired" in data["detail"]

    async def test_reset_password_weak_password(self, client: AsyncClient):
        """Test resetting password with weak password"""
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": "some-token",
                "new_password": "weak"
            }
        )

        # Should fail validation (password too short)
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.password_reset
class TestPasswordResetIntegration:
    """Integration tests for complete password reset flow"""

    async def test_complete_password_reset_flow_manual(self, client: AsyncClient, registered_user, db_session):
        """
        Test complete password reset flow (requires manual token extraction)

        This test demonstrates the full flow but skips actual execution
        since it requires email service mocking.
        """
        pytest.skip("Full integration test requires email service mock")

        # The flow would be:
        # 1. Register user (done via fixture)
        # 2. Request password reset
        # 3. Extract token from database or mock email
        # 4. Verify token
        # 5. Reset password
        # 6. Login with new password
        # 7. Try to reuse token (should fail)


@pytest.mark.asyncio
@pytest.mark.auth
class TestAuthEndpoints:
    """Basic auth endpoint tests"""

    async def test_register_user(self, client: AsyncClient, test_user_data):
        """Test user registration"""
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == test_user_data["admin_email"]

    async def test_register_duplicate_email(self, client: AsyncClient, registered_user, test_user_data):
        """Test registering with duplicate email"""
        # Try to register again with same email
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    async def test_login_success(self, client: AsyncClient, test_user_data, registered_user):
        """Test successful login"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["admin_email"],
                "password": test_user_data["admin_password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data, registered_user):
        """Test login with wrong password"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["admin_email"],
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid" in data["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123"
            }
        )

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, registered_user):
        """Test getting current user info"""
        # Get access token from registration
        access_token = registered_user["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user["user"]["email"]

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


@pytest.mark.asyncio
class TestHealthCheck:
    """Test health check endpoint"""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
