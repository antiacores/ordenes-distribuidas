import subprocess
import json
import sys
import time

print("Esperando a que los servicios estén saludables...")

for _ in range(24):  # 24 intentos x 5 segundos = 120 segundos max
    result = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        capture_output=True, text=True
    )
    services = [json.loads(line) for line in result.stdout.strip().split("\n") if line]
    unhealthy = [s["Name"] for s in services if s.get("Health") not in ("healthy", "")]
    if not unhealthy:
        print("Todos los servicios están saludables.")
        sys.exit(0)
    print(f"Esperando: {unhealthy}")
    time.sleep(5)

print("Timeout: algunos servicios no están saludables.")
sys.exit(1)