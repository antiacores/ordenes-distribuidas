#!/bin/bash

# ============================================================
# Integration tests
# ============================================================

set -e  # Si algo falla, para todo

BASE_URL="http://localhost:8000"
PASS=0
FAIL=0

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ $1${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}✗ $1${NC}"; FAIL=$((FAIL+1)); }

check_status() {
    local description=$1
    local expected=$2
    local actual=$3
    if [ "$actual" -eq "$expected" ]; then
        pass "$description (HTTP $actual)"
    else
        fail "$description — esperado HTTP $expected, obtenido HTTP $actual"
    fi
}

echo "============================================================"
echo "Corriendo pruebas de integración..."
echo "============================================================"

# ------------------------------------------------------------
# 1. SIGNUP customer
# ------------------------------------------------------------
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","name":"Test","password":"123456"}')
check_status "Signup customer" 200 $STATUS

# ------------------------------------------------------------
# 2. LOGIN customer
# ------------------------------------------------------------
RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}')
TOKEN=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

if [ -n "$TOKEN" ]; then
    pass "Login customer — token recibido"
else
    fail "Login customer — no se recibió token"
    exit 1
fi

# ------------------------------------------------------------
# 3. Crear orden con token
# ------------------------------------------------------------
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"customer":"Test","items":[{"sku":"CAM-BLN-M","qty":1}]}')
STATUS=$(echo "$RESPONSE" | tail -1)
ORDER_ID=$(echo "$RESPONSE" | head -1 | python3 -c "import sys,json; print(json.load(sys.stdin)['order_id'])")
check_status "Crear orden con token" 202 $STATUS

# ------------------------------------------------------------
# 4. Crear orden sin token (debe fallar)
# ------------------------------------------------------------
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE_URL/orders \
  -H "Content-Type: application/json" \
  -d '{"customer":"Test","items":[{"sku":"CAM-BLN-M","qty":1}]}')
check_status "Crear orden sin token (debe fallar)" 422 $STATUS

# ------------------------------------------------------------
# 5. Esperar a que la orden se procese
# ------------------------------------------------------------
echo "Esperando 5 segundos para que se procese la orden..."
sleep 5

# ------------------------------------------------------------
# 6. Consultar orden con token
# ------------------------------------------------------------
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/orders/$ORDER_ID \
  -H "Authorization: Bearer $TOKEN")
check_status "Consultar orden propia" 200 $STATUS

# ------------------------------------------------------------
# 7. Login inválido
# ------------------------------------------------------------
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"wrongpassword"}')
check_status "Login con password incorrecto (debe fallar)" 500 $STATUS

# ------------------------------------------------------------
# 8. Signup admin sin ser admin (debe fallar)
# ------------------------------------------------------------
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE_URL/auth/signup/admin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"username":"hacker","email":"hacker@test.com","name":"Hacker","password":"123456"}')
check_status "Signup admin sin ser admin (debe fallar)" 500 $STATUS

# ------------------------------------------------------------
# 9. Token inválido
# ------------------------------------------------------------
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/orders/$ORDER_ID \
  -H "Authorization: Bearer tokenfalso123")
check_status "Token inválido (debe fallar)" 401 $STATUS

# ------------------------------------------------------------
# Resumen
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo -e "Resultados: ${GREEN}$PASS pasaron${NC} | ${RED}$FAIL fallaron${NC}"
echo "============================================================"

if [ $FAIL -gt 0 ]; then
    exit 1
fi