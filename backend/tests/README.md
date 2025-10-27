# Backend Tests

## Setup

1. Install test dependencies:
```bash
cd backend
pip install -r requirements-dev.txt
```

2. Create test database:
```bash
# Using psql
createdb -h localhost -U postgres bc_legal_test

# Or using docker
docker exec -it bc-legal-postgres psql -U postgres -c "CREATE DATABASE bc_legal_test;"
```

## Running Tests

### Using VS Code Test Explorer (Recommended!)

1. Open VS Code
2. Click the "Testing" icon in the sidebar (flask icon)
3. VS Code will auto-discover all tests
4. Click ▶️ to run individual tests or test classes
5. See results inline with green ✅ or red ❌

**Benefits:**
- Visual test results
- Run individual tests with one click
- Debug tests with breakpoints
- See coverage inline

### Using Command Line

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_auth_password_reset.py
```

Run specific test:
```bash
pytest tests/test_auth_password_reset.py::TestPasswordReset::test_request_password_reset_success
```

Run tests with markers:
```bash
pytest -m auth          # Run only auth tests
pytest -m password_reset # Run only password reset tests
pytest -m "not slow"    # Skip slow tests
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to see coverage report
```

Verbose output:
```bash
pytest -v -s
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                      # Fixtures and configuration
├── test_auth_password_reset.py     # Auth & password reset tests
└── README.md                        # This file
```

## Available Fixtures

- `client`: Async HTTP client for testing endpoints
- `db_session`: Test database session
- `test_user_data`: Sample user data
- `registered_user`: Pre-registered test user

## Writing New Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestMyFeature:
    async def test_something(self, client: AsyncClient):
        response = await client.get("/api/v1/my-endpoint")
        assert response.status_code == 200
```

## Markers

Available pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.password_reset` - Password reset tests
- `@pytest.mark.slow` - Slow tests (can be skipped)

## Debugging Tests in VS Code

1. Set a breakpoint in your test (click left of line number)
2. Right-click the test in Test Explorer
3. Select "Debug Test"
4. Debugger will stop at your breakpoint

## CI/CD Integration

Tests can be run in CI/CD pipelines:
```yaml
# Example for GitHub Actions
- name: Run tests
  run: |
    cd backend
    pip install -r requirements-dev.txt
    pytest --cov=app --cov-report=xml
```

## Tips

- **Fast feedback**: Run tests on save by enabling "Run Tests on Save" in VS Code
- **Focus**: Use `-k "test_name"` to run tests matching a pattern
- **Parallel**: Use `pytest -n auto` (requires pytest-xdist) for parallel execution
- **Watch mode**: Use `pytest-watch` for continuous testing

## Troubleshooting

**Tests not discovered?**
- Make sure pytest is installed: `pip install pytest`
- Check Python interpreter in VS Code (bottom-left)
- Reload VS Code window: Ctrl+Shift+P → "Reload Window"

**Database connection errors?**
- Make sure PostgreSQL is running: `docker ps`
- Create test database: `createdb bc_legal_test`
- Check connection string in `conftest.py`

**Import errors?**
- Make sure you're in the `backend` directory
- Check PYTHONPATH includes backend directory
