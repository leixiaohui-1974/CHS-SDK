"""端到端测试

测试完整的用户工作流程和系统集成。
"""

import asyncio
import pytest
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

import aiohttp
import websockets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# 测试配置
TEST_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",
    "websocket_url": "ws://localhost:8000/ws",
    "test_timeout": 30,
    "selenium_timeout": 10
}

# 测试用户数据
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123",
    "username": "testuser"
}

# 测试仿真配置
TEST_SIMULATION = {
    "name": "E2E Test Simulation",
    "description": "End-to-end test simulation",
    "duration": 3600,
    "time_step": 60,
    "config": {
        "nodes": [
            {
                "id": "reservoir_1",
                "type": "reservoir",
                "initial_level": 10.0,
                "capacity": 100.0
            },
            {
                "id": "pump_1",
                "type": "pump",
                "max_flow_rate": 5.0,
                "efficiency": 0.85
            }
        ],
        "connections": [
            {
                "from": "reservoir_1",
                "to": "pump_1",
                "type": "pipe"
            }
        ]
    }
}


class E2ETestSuite:
    """端到端测试套件"""
    
    def __init__(self):
        self.session = None
        self.driver = None
        self.auth_token = None
        self.simulation_id = None
    
    async def setup(self):
        """测试设置"""
        # 创建HTTP会话
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TEST_CONFIG["test_timeout"])
        )
        
        # 设置Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(TEST_CONFIG["selenium_timeout"])
    
    async def teardown(self):
        """测试清理"""
        if self.session:
            await self.session.close()
        
        if self.driver:
            self.driver.quit()
    
    async def test_user_registration_and_login(self) -> bool:
        """测试用户注册和登录流程"""
        try:
            # 1. 注册用户
            register_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "username": TEST_USER["username"]
            }
            
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/auth/register",
                json=register_data
            ) as response:
                if response.status not in [200, 201, 409]:  # 409 for already exists
                    return False
            
            # 2. 登录用户
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/auth/login",
                json=login_data
            ) as response:
                if response.status != 200:
                    return False
                
                result = await response.json()
                self.auth_token = result.get("access_token")
                
                if not self.auth_token:
                    return False
            
            # 3. 验证token
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/auth/me",
                headers=headers
            ) as response:
                return response.status == 200
        
        except Exception as e:
            print(f"用户注册和登录测试失败: {e}")
            return False
    
    async def test_simulation_lifecycle(self) -> bool:
        """测试仿真生命周期"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # 1. 创建仿真
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/simulation/sessions",
                json=TEST_SIMULATION,
                headers=headers
            ) as response:
                if response.status not in [200, 201]:
                    return False
                
                result = await response.json()
                self.simulation_id = result.get("id")
                
                if not self.simulation_id:
                    return False
            
            # 2. 启动仿真
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/simulation/sessions/{self.simulation_id}/start",
                headers=headers
            ) as response:
                if response.status != 200:
                    return False
            
            # 3. 等待仿真运行
            await asyncio.sleep(5)
            
            # 4. 检查仿真状态
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/simulation/sessions/{self.simulation_id}",
                headers=headers
            ) as response:
                if response.status != 200:
                    return False
                
                result = await response.json()
                status = result.get("status")
                
                if status not in ["running", "completed"]:
                    return False
            
            # 5. 停止仿真
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/simulation/sessions/{self.simulation_id}/stop",
                headers=headers
            ) as response:
                return response.status == 200
        
        except Exception as e:
            print(f"仿真生命周期测试失败: {e}")
            return False
    
    async def test_websocket_communication(self) -> bool:
        """测试WebSocket通信"""
        try:
            # 连接WebSocket
            uri = f"{TEST_CONFIG['websocket_url']}/simulation/{self.simulation_id}"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                # 发送消息
                test_message = {
                    "type": "subscribe",
                    "data": {"events": ["simulation_update", "node_update"]}
                }
                
                await websocket.send(str(test_message))
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    return bool(response)
                except asyncio.TimeoutError:
                    return False
        
        except Exception as e:
            print(f"WebSocket通信测试失败: {e}")
            return False
    
    def test_frontend_navigation(self) -> bool:
        """测试前端页面导航"""
        try:
            # 1. 访问首页
            self.driver.get(TEST_CONFIG["frontend_url"])
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 2. 检查登录页面
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登录') or contains(text(), 'Login')]")
            if not login_button:
                return False
            
            # 3. 执行登录
            email_input = self.driver.find_element(By.NAME, "email")
            password_input = self.driver.find_element(By.NAME, "password")
            
            email_input.send_keys(TEST_USER["email"])
            password_input.send_keys(TEST_USER["password"])
            login_button.click()
            
            # 4. 等待登录成功
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard') or contains(@class, 'main')]")),
            )
            
            # 5. 导航到仿真页面
            simulation_link = self.driver.find_element(By.XPATH, "//a[contains(text(), '仿真') or contains(text(), 'Simulation')]")
            simulation_link.click()
            
            # 6. 检查仿真页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'simulation')]")),
            )
            
            return True
        
        except (TimeoutException, Exception) as e:
            print(f"前端导航测试失败: {e}")
            return False
    
    def test_simulation_ui_interaction(self) -> bool:
        """测试仿真UI交互"""
        try:
            # 1. 创建新仿真
            create_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '创建') or contains(text(), 'Create')]")
            create_button.click()
            
            # 2. 填写仿真表单
            name_input = self.driver.find_element(By.NAME, "name")
            name_input.send_keys(TEST_SIMULATION["name"])
            
            description_input = self.driver.find_element(By.NAME, "description")
            description_input.send_keys(TEST_SIMULATION["description"])
            
            # 3. 提交表单
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            
            # 4. 等待仿真创建成功
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{TEST_SIMULATION['name']}')]")),
            )
            
            # 5. 启动仿真
            start_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '启动') or contains(text(), 'Start')]")
            start_button.click()
            
            # 6. 检查仿真状态
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '运行中') or contains(text(), 'Running')]")),
            )
            
            return True
        
        except (TimeoutException, Exception) as e:
            print(f"仿真UI交互测试失败: {e}")
            return False
    
    async def test_performance_monitoring(self) -> bool:
        """测试性能监控"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # 1. 获取性能指标
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/performance/metrics",
                headers=headers
            ) as response:
                if response.status != 200:
                    return False
                
                metrics = await response.json()
                required_fields = ["system", "application", "timestamp"]
                
                for field in required_fields:
                    if field not in metrics:
                        return False
            
            # 2. 获取系统健康状态
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/performance/health",
                headers=headers
            ) as response:
                if response.status != 200:
                    return False
                
                health = await response.json()
                if "status" not in health:
                    return False
            
            # 3. 获取Prometheus指标
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/performance/prometheus",
                headers=headers
            ) as response:
                return response.status == 200
        
        except Exception as e:
            print(f"性能监控测试失败: {e}")
            return False
    
    async def test_data_persistence(self) -> bool:
        """测试数据持久化"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # 1. 获取仿真结果
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/simulation/sessions/{self.simulation_id}/results",
                headers=headers
            ) as response:
                if response.status != 200:
                    return False
                
                results = await response.json()
                if not results:
                    return False
            
            # 2. 获取仿真历史
            async with self.session.get(
                f"{TEST_CONFIG['api_base_url']}/api/simulation/sessions",
                headers=headers
            ) as response:
                if response.status != 200:
                    return False
                
                sessions = await response.json()
                
                # 检查我们的测试仿真是否在列表中
                test_session_found = any(
                    session.get("id") == self.simulation_id 
                    for session in sessions.get("items", [])
                )
                
                return test_session_found
        
        except Exception as e:
            print(f"数据持久化测试失败: {e}")
            return False
    
    async def run_full_test_suite(self) -> Dict[str, bool]:
        """运行完整的测试套件"""
        results = {}
        
        try:
            await self.setup()
            
            # 运行所有测试
            test_methods = [
                ("user_registration_and_login", self.test_user_registration_and_login),
                ("simulation_lifecycle", self.test_simulation_lifecycle),
                ("websocket_communication", self.test_websocket_communication),
                ("frontend_navigation", lambda: self.test_frontend_navigation()),
                ("simulation_ui_interaction", lambda: self.test_simulation_ui_interaction()),
                ("performance_monitoring", self.test_performance_monitoring),
                ("data_persistence", self.test_data_persistence)
            ]
            
            for test_name, test_method in test_methods:
                print(f"运行测试: {test_name}")
                try:
                    if asyncio.iscoroutinefunction(test_method):
                        result = await test_method()
                    else:
                        result = test_method()
                    
                    results[test_name] = result
                    print(f"测试 {test_name}: {'通过' if result else '失败'}")
                    
                    # 如果关键测试失败，停止后续测试
                    if not result and test_name in ["user_registration_and_login", "simulation_lifecycle"]:
                        print(f"关键测试 {test_name} 失败，停止后续测试")
                        break
                
                except Exception as e:
                    print(f"测试 {test_name} 执行异常: {e}")
                    results[test_name] = False
                
                # 测试间隔
                await asyncio.sleep(2)
        
        finally:
            await self.teardown()
        
        return results


# pytest测试函数
@pytest.mark.asyncio
async def test_e2e_full_suite():
    """完整的端到端测试套件"""
    test_suite = E2ETestSuite()
    results = await test_suite.run_full_test_suite()
    
    # 检查测试结果
    failed_tests = [test for test, result in results.items() if not result]
    
    if failed_tests:
        pytest.fail(f"以下测试失败: {', '.join(failed_tests)}")
    
    print("所有端到端测试通过！")


@pytest.mark.asyncio
async def test_api_endpoints():
    """API端点测试"""
    test_suite = E2ETestSuite()
    await test_suite.setup()
    
    try:
        # 测试用户认证
        auth_result = await test_suite.test_user_registration_and_login()
        assert auth_result, "用户认证测试失败"
        
        # 测试仿真API
        simulation_result = await test_suite.test_simulation_lifecycle()
        assert simulation_result, "仿真API测试失败"
        
        # 测试性能监控API
        performance_result = await test_suite.test_performance_monitoring()
        assert performance_result, "性能监控API测试失败"
    
    finally:
        await test_suite.teardown()


@pytest.mark.asyncio
async def test_websocket_functionality():
    """WebSocket功能测试"""
    test_suite = E2ETestSuite()
    await test_suite.setup()
    
    try:
        # 先进行认证
        auth_result = await test_suite.test_user_registration_and_login()
        assert auth_result, "用户认证失败"
        
        # 创建仿真
        simulation_result = await test_suite.test_simulation_lifecycle()
        assert simulation_result, "仿真创建失败"
        
        # 测试WebSocket
        websocket_result = await test_suite.test_websocket_communication()
        assert websocket_result, "WebSocket通信测试失败"
    
    finally:
        await test_suite.teardown()


def test_frontend_ui():
    """前端UI测试"""
    test_suite = E2ETestSuite()
    
    # 同步设置
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_suite.setup())
    
    try:
        # 测试前端导航
        navigation_result = test_suite.test_frontend_navigation()
        assert navigation_result, "前端导航测试失败"
        
        # 测试UI交互
        ui_result = test_suite.test_simulation_ui_interaction()
        assert ui_result, "UI交互测试失败"
    
    finally:
        loop.run_until_complete(test_suite.teardown())
        loop.close()


if __name__ == "__main__":
    # 运行完整测试套件
    async def main():
        test_suite = E2ETestSuite()
        results = await test_suite.run_full_test_suite()
        
        print("\n=== 端到端测试结果 ===")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n总计: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
        
        return passed_tests == total_tests
    
    # 运行测试
    success = asyncio.run(main())
    exit(0 if success else 1)