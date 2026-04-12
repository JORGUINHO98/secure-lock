#!/bin/bash

# Health Check Script - Secure Lock Backend
# Uso: bash health_check.sh
# O hacerlo ejecutable: chmod +x health_check.sh && ./health_check.sh

set -e

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔍  HEALTH CHECK - SECURE LOCK BACKEND"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

check_service() {
    local service_name=$1
    local check_cmd=$2
    local description=$3
    
    echo -n "📌 $description... "
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}"
        ((FAILED++))
    fi
}

# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}1. DOCKER SERVICES${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "docker-compose" "docker-compose ps -q | wc -l | grep -q '[1-9]'" "Docker Compose running"

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}2. INFRASTRUCTURE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "PostgreSQL-Healthy" "docker-compose exec -T db pg_isready -U admin" "PostgreSQL healthy"
check_service "PostgreSQL-Conn" "docker-compose exec -T db psql -U admin -d secure_lock -c 'SELECT 1;'" "PostgreSQL accessible"

check_service "Redis-Ping" "docker-compose exec -T redis redis-cli ping | grep -q PONG" "Redis responding"

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}3. DATABASE INTEGRITY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count tables
TABLES=$(docker-compose exec -T db psql -U admin -d secure_lock -c "\dt" 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
check_service "Tables" "[ '$TABLES' -ge 10 ]" "Database tables (found: $TABLES)"

# Check migrations
check_service "Migrations" "docker-compose exec -T db psql -U admin -d secure_lock -c 'SELECT COUNT(*) FROM django_migrations;' | grep -q '[1-9]'" "Migration applied"

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}4. BACKEND SERVICE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "Backend-Running" "docker-compose ps backend | grep -q 'Up'" "Backend container running"
check_service "Backend-Port" "netstat -an 2>/dev/null | grep -q '8000' || lsof -i :8000" "Backend port 8000 open" || echo -e "${YELLOW}⚠️  (netstat/lsof not available, skipping)${NC}" && ((PASSED++))

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}5. CELERY WORKERS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "Celery-Worker" "docker-compose ps celery_worker | grep -q 'Up'" "Celery worker running"
check_service "Celery-Beat" "docker-compose ps celery_beat | grep -q 'Up'" "Celery beat running"

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}6. DJANGO CONFIGURATION${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "Settings" "docker-compose exec backend python -c 'import django; django.setup()'" "Django settings loaded"

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}7. VOLUMES & STORAGE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "Volume-PostgreSQL" "docker volume ls | grep -q postgres_data" "PostgreSQL volume exists"
check_service "Volume-Redis" "docker volume ls | grep -q redis_data" "Redis volume exists"

# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}8. OPTIONAL CHECKS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get DB size
DB_SIZE=$(docker-compose exec -T db psql -U admin -d secure_lock -c "SELECT pg_size_pretty(pg_database_size('secure_lock'));" 2>/dev/null | tail -1 | tr -d ' ')
if [ -n "$DB_SIZE" ]; then
    echo -e "📊 Database size: ${BLUE}$DB_SIZE${NC}"
fi

# Get Redis memory
REDIS_MEM=$(docker-compose exec -T redis redis-cli INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d $'\r')
if [ -n "$REDIS_MEM" ]; then
    echo -e "💾 Redis memory: ${BLUE}$REDIS_MEM${NC}"
fi

# Get table count
echo -e "📋 Tables in database: ${BLUE}$TABLES${NC}"

# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "📊 SUMMARY: ${GREEN}$PASSED Passed${NC} | ${RED}$FAILED Failed${NC}"
echo "═══════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - System is healthy!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAILED checks failed - Review logs above${NC}"
    echo ""
    echo "Common issues:"
    echo "  • docker-compose services not running: docker-compose up -d"
    echo "  • Database issues: docker-compose logs db"
    echo "  • Backend errors: docker-compose logs backend"
    echo ""
    exit 1
fi
