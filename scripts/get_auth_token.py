import sys
import os
from datetime import datetime, timedelta
from jose import jwt

# Add backend to path to allow imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.core.config.settings import settings

def generate_token():
    secret_key = settings.CLERK_SECRET_KEY
    
    payload = {
        "sub": "user_test_123",
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iss": "https://clerk.codeguard.ai",
        "name": "Test User",
        "email": "test@codeguard.ai",
        "role": "developer"
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

if __name__ == "__main__":
    try:
        token = generate_token()
        print("\n✅ Token generado exitosamente:")
        print(f"Bearer {token}")
        print("\n📋 Copia este valor y úsalo en el botón 'Authorize' de Swagger UI (http://127.0.0.1:8000/docs)")
        print("O usa este comando curl:")
        print(f'curl -X POST "http://127.0.0.1:8000/api/v1/analyze" -H "Authorization: Bearer {token}" -F "file=@backend/tests/integration/test_quality_agent_integration.py"')
    except Exception as e:
        print(f"Error generando token: {e}")
