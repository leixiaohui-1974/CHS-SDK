"""认证 API 端点测试

测试用户认证、授权、令牌管理等相关的 API 端点。
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta
from jose import jwt

# 导入应用
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from server import app
from auth.authentication import create_access_token, verify_password, get_password_hash
from auth.dependencies import get_current_active_user
from database.models import UserDB
from core.config import settings

# 创建测试客户端
client = TestClient(app)

# 测试用户数据
TEST_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
}

TEST_ADMIN_DATA = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "adminpassword123",
    "full_name": "Admin User"
}

class TestUserRegistration:
    """用户注册测试"""
    
    @patch('database.crud.create_user')
    @patch('database.crud.get_user_by_email')
    @patch('database.crud.get_user_by_username')
    def test_register_success(self, mock_get_by_username, mock_get_by_email, mock_create_user):
        """测试用户注册成功"""
        # 模拟用户不存在
        mock_get_by_username.return_value = None
        mock_get_by_email.return_value = None
        
        # 模拟创建用户成功
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.username = TEST_USER_DATA["username"]
        mock_user.email = TEST_USER_DATA["email"]
        mock_user.full_name = TEST_USER_DATA["full_name"]
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_create_user.return_value = mock_user
        
        response = client.post("/api/auth/register", json=TEST_USER_DATA)
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["username"] == TEST_USER_DATA["username"]
        assert data["email"] == TEST_USER_DATA["email"]
        assert data["full_name"] == TEST_USER_DATA["full_name"]
        assert "password" not in data  # 密码不应该返回
    
    @patch('database.crud.get_user_by_username')
    def test_register_username_exists(self, mock_get_by_username):
        """测试用户名已存在"""
        # 模拟用户名已存在
        mock_user = MagicMock(spec=UserDB)
        mock_get_by_username.return_value = mock_user
        
        response = client.post("/api/auth/register", json=TEST_USER_DATA)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @patch('database.crud.get_user_by_email')
    @patch('database.crud.get_user_by_username')
    def test_register_email_exists(self, mock_get_by_username, mock_get_by_email):
        """测试邮箱已存在"""
        # 模拟用户名不存在，但邮箱已存在
        mock_get_by_username.return_value = None
        mock_user = MagicMock(spec=UserDB)
        mock_get_by_email.return_value = mock_user
        
        response = client.post("/api/auth/register", json=TEST_USER_DATA)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_invalid_data(self):
        """测试无效注册数据"""
        invalid_data = {
            "username": "",  # 空用户名
            "email": "invalid-email",  # 无效邮箱
            "password": "123"  # 密码太短
        }
        
        response = client.post("/api/auth/register", json=invalid_data)
        assert response.status_code == 422  # 验证错误

class TestUserLogin:
    """用户登录测试"""
    
    @patch('database.crud.get_user_by_username')
    def test_login_success(self, mock_get_user):
        """测试登录成功"""
        # 模拟用户存在且密码正确
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.username = TEST_USER_DATA["username"]
        mock_user.email = TEST_USER_DATA["email"]
        mock_user.hashed_password = get_password_hash(TEST_USER_DATA["password"])
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_get_user.return_value = mock_user
        
        login_data = {
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # 验证令牌
        token = data["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == TEST_USER_DATA["username"]
    
    @patch('database.crud.get_user_by_username')
    def test_login_wrong_password(self, mock_get_user):
        """测试密码错误"""
        # 模拟用户存在但密码错误
        mock_user = MagicMock(spec=UserDB)
        mock_user.hashed_password = get_password_hash("different_password")
        mock_user.is_active = True
        mock_get_user.return_value = mock_user
        
        login_data = {
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @patch('database.crud.get_user_by_username')
    def test_login_user_not_found(self, mock_get_user):
        """测试用户不存在"""
        mock_get_user.return_value = None
        
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @patch('database.crud.get_user_by_username')
    def test_login_inactive_user(self, mock_get_user):
        """测试非活跃用户登录"""
        # 模拟用户存在但未激活
        mock_user = MagicMock(spec=UserDB)
        mock_user.hashed_password = get_password_hash(TEST_USER_DATA["password"])
        mock_user.is_active = False
        mock_get_user.return_value = mock_user
        
        login_data = {
            "username": TEST_USER_DATA["username"],
            "password": TEST_USER_DATA["password"]
        }
        
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]

class TestTokenValidation:
    """令牌验证测试"""
    
    def test_valid_token(self):
        """测试有效令牌"""
        # 创建有效令牌
        token_data = {"sub": TEST_USER_DATA["username"]}
        token = create_access_token(data=token_data)
        
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('database.crud.get_user_by_username') as mock_get_user:
            mock_user = MagicMock(spec=UserDB)
            mock_user.username = TEST_USER_DATA["username"]
            mock_user.is_active = True
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/auth/me", headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["username"] == TEST_USER_DATA["username"]
    
    def test_invalid_token(self):
        """测试无效令牌"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_expired_token(self):
        """测试过期令牌"""
        # 创建过期令牌
        token_data = {"sub": TEST_USER_DATA["username"]}
        expired_token = create_access_token(
            data=token_data, 
            expires_delta=timedelta(minutes=-1)  # 负数表示已过期
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_missing_token(self):
        """测试缺少令牌"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

class TestUserProfile:
    """用户资料测试"""
    
    @patch('auth.dependencies.get_current_active_user')
    def test_get_current_user(self, mock_current_user):
        """测试获取当前用户信息"""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.username = TEST_USER_DATA["username"]
        mock_user.email = TEST_USER_DATA["email"]
        mock_user.full_name = TEST_USER_DATA["full_name"]
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_current_user.return_value = mock_user
        
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["username"] == TEST_USER_DATA["username"]
        assert data["email"] == TEST_USER_DATA["email"]
        assert data["full_name"] == TEST_USER_DATA["full_name"]
        assert "password" not in data
        assert "hashed_password" not in data
    
    @patch('auth.dependencies.get_current_active_user')
    @patch('database.crud.update_user')
    def test_update_user_profile(self, mock_update_user, mock_current_user):
        """测试更新用户资料"""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        mock_user.username = TEST_USER_DATA["username"]
        mock_user.email = TEST_USER_DATA["email"]
        mock_current_user.return_value = mock_user
        
        # 模拟更新后的用户
        updated_user = MagicMock(spec=UserDB)
        updated_user.id = 1
        updated_user.username = TEST_USER_DATA["username"]
        updated_user.email = "new@example.com"
        updated_user.full_name = "Updated Name"
        mock_update_user.return_value = updated_user
        
        update_data = {
            "email": "new@example.com",
            "full_name": "Updated Name"
        }
        
        response = client.put("/api/auth/me", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["full_name"] == "Updated Name"

class TestPasswordManagement:
    """密码管理测试"""
    
    @patch('auth.dependencies.get_current_active_user')
    @patch('database.crud.update_user_password')
    def test_change_password_success(self, mock_update_password, mock_current_user):
        """测试修改密码成功"""
        mock_user = MagicMock(spec=UserDB)
        mock_user.hashed_password = get_password_hash("old_password")
        mock_current_user.return_value = mock_user
        mock_update_password.return_value = True
        
        password_data = {
            "current_password": "old_password",
            "new_password": "new_password123"
        }
        
        response = client.post("/api/auth/change-password", json=password_data)
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]
    
    @patch('auth.dependencies.get_current_active_user')
    def test_change_password_wrong_current(self, mock_current_user):
        """测试当前密码错误"""
        mock_user = MagicMock(spec=UserDB)
        mock_user.hashed_password = get_password_hash("old_password")
        mock_current_user.return_value = mock_user
        
        password_data = {
            "current_password": "wrong_password",
            "new_password": "new_password123"
        }
        
        response = client.post("/api/auth/change-password", json=password_data)
        assert response.status_code == 400
        assert "Incorrect password" in response.json()["detail"]

class TestAdminEndpoints:
    """管理员端点测试"""
    
    @patch('auth.dependencies.get_current_active_user')
    def test_admin_only_endpoint_success(self, mock_current_user):
        """测试管理员端点访问成功"""
        mock_admin = MagicMock(spec=UserDB)
        mock_admin.is_superuser = True
        mock_current_user.return_value = mock_admin
        
        response = client.get("/api/auth/admin/users")
        assert response.status_code == 200
    
    @patch('auth.dependencies.get_current_active_user')
    def test_admin_only_endpoint_forbidden(self, mock_current_user):
        """测试非管理员访问管理员端点"""
        mock_user = MagicMock(spec=UserDB)
        mock_user.is_superuser = False
        mock_current_user.return_value = mock_user
        
        response = client.get("/api/auth/admin/users")
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

class TestAuthenticationUtils:
    """认证工具函数测试"""
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # 验证哈希不等于原密码
        assert hashed != password
        
        # 验证密码验证
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_token_creation(self):
        """测试令牌创建"""
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        
        # 验证令牌不为空
        assert token is not None
        assert len(token) > 0
        
        # 验证令牌可以解码
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_token_expiration(self):
        """测试令牌过期时间"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data=data, expires_delta=expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_timestamp = payload["exp"]
        
        # 验证过期时间大约是30分钟后
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.fromtimestamp(exp_timestamp)
        
        # 允许1分钟的误差
        time_diff = abs((actual_exp - expected_exp).total_seconds())
        assert time_diff < 60

if __name__ == "__main__":
    pytest.main([__file__])