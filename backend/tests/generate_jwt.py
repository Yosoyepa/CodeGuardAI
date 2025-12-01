from datetime import datetime, timedelta

from jose import jwt

# Simula el JWT que Clerk genera con el template "supabase"
token = jwt.encode(
    {
        # Claims automáticos de Clerk (siempre incluidos)
        "sub": "user_36E0_CjDHVmkse",  # user.id - Clerk lo agrega automáticamente
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int(
            (datetime.utcnow() + timedelta(seconds=60)).timestamp()
        ),  # 60s como en tu template
        "iss": "https://enabled-cattle-58.clerk.accounts.dev",
        # Claims personalizados de tu template
        "name": "test backend",
        "role": "authenticated",
        "email": "testbackend@codeguard.ai",
        "app_metadata": {},
        "user_metadata": {},
    },
    "sk_test_hwourB8W6TcFQwgvcmMln6lwFZSUwesWOD8zSWbteZ",
    algorithm="HS256",
)

print("Token JWT:")
print(token)
print("\n--- Para probar con cURL ---")
print(
    f'curl -X POST "http://localhost:8000/api/v1/auth/login" -H "Content-Type: application/json" -d \'{{"token": "{token}"}}\''
)
