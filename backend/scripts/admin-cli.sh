#!/bin/bash
# SR&ED Intelligence - Admin CLI
# Interactive script for testing admin endpoints

BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

print_header() {
    clear
    echo -e "${CYAN}========================================"
    echo -e "  SR&ED Intelligence - Admin CLI"
    echo -e "========================================${NC}"
    echo ""
}

get_credentials() {
    echo -e "${YELLOW}Enter your admin credentials:${NC}"
    read -p "Email: " EMAIL
    read -sp "Password: " PASSWORD
    echo ""
}

get_token() {
    local response
    response=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

    # Token is nested under .token.access_token
    TOKEN=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('token', {}).get('access_token', '') or d.get('access_token', ''))" 2>/dev/null)

    if [ -n "$TOKEN" ]; then
        echo -e "\n${GREEN}Authentication successful!${NC}"
        return 0
    else
        echo -e "\n${RED}Authentication failed: $response${NC}"
        return 1
    fi
}

call_api() {
    local endpoint=$1
    local method=${2:-GET}

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Not authenticated. Please login first.${NC}"
        return 1
    fi

    curl -s -X "$method" "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null || \
    curl -s -X "$method" "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $TOKEN"
}

# Menu Commands
get_usage_summary() {
    echo -e "\n${CYAN}--- Usage Summary ---${NC}"
    read -p "Days to look back (default: 30): " days
    days=${days:-30}
    call_api "/api/v1/admin/usage?days=$days"
}

get_usage_by_company() {
    echo -e "\n${CYAN}--- Usage by Company ---${NC}"
    read -p "Company ID (UUID): " company_id
    read -p "Days to look back (default: 30): " days
    days=${days:-30}
    call_api "/api/v1/admin/usage?days=$days&company_id=$company_id"
}

get_daily_usage() {
    echo -e "\n${CYAN}--- Daily Usage ---${NC}"
    read -p "Days to look back (default: 30): " days
    days=${days:-30}
    call_api "/api/v1/admin/usage/daily?days=$days"
}

get_daily_usage_by_service() {
    echo -e "\n${CYAN}--- Daily Usage by Service ---${NC}"
    echo "Services: claude_chat, claude_summary, openai_embeddings, textract_ocr"
    read -p "Service name: " service
    read -p "Days to look back (default: 30): " days
    days=${days:-30}
    call_api "/api/v1/admin/usage/daily?days=$days&service=$service"
}

get_companies() {
    echo -e "\n${CYAN}--- All Companies ---${NC}"
    call_api "/api/v1/admin/companies"
}

get_feedback_stats() {
    echo -e "\n${CYAN}--- Feedback Statistics ---${NC}"
    read -p "Days to look back (default: 30): " days
    days=${days:-30}
    call_api "/api/v1/admin/feedback/stats?days=$days"
}

get_feedback_stats_by_company() {
    echo -e "\n${CYAN}--- Feedback Stats by Company ---${NC}"
    read -p "Company ID (UUID): " company_id
    read -p "Days to look back (default: 7): " days
    days=${days:-7}
    call_api "/api/v1/admin/feedback/stats?days=$days&company_id=$company_id"
}

get_quality_alerts() {
    echo -e "\n${CYAN}--- Active Quality Alerts ---${NC}"
    call_api "/api/v1/admin/feedback/alerts"
}

get_flagged_messages() {
    echo -e "\n${CYAN}--- Flagged Messages ---${NC}"
    read -p "Limit (default: 50): " limit
    limit=${limit:-50}
    call_api "/api/v1/admin/feedback/flagged?limit=$limit"
}

trigger_alert_check() {
    echo -e "\n${CYAN}--- Trigger Alert Check ---${NC}"
    call_api "/api/v1/admin/feedback/check-alerts" "POST"
}

show_menu() {
    echo ""
    echo -e "${YELLOW}COST REPORTING${NC}"
    echo "  1. Get usage summary"
    echo "  2. Get usage by company"
    echo "  3. Get daily usage"
    echo "  4. Get daily usage by service"
    echo "  5. List all companies"
    echo ""
    echo -e "${YELLOW}FEEDBACK ANALYTICS${NC}"
    echo "  6. Get feedback statistics"
    echo "  7. Get feedback stats by company"
    echo "  8. Get active quality alerts"
    echo "  9. Get flagged messages"
    echo " 10. Trigger alert check"
    echo ""
    echo -e "${YELLOW}OTHER${NC}"
    echo "  r. Re-authenticate"
    echo "  q. Quit"
    echo ""
}

# Main
print_header
get_credentials
get_token

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to authenticate. Exiting.${NC}"
    exit 1
fi

while true; do
    show_menu
    read -p "Select option: " choice

    case $choice in
        1) get_usage_summary ;;
        2) get_usage_by_company ;;
        3) get_daily_usage ;;
        4) get_daily_usage_by_service ;;
        5) get_companies ;;
        6) get_feedback_stats ;;
        7) get_feedback_stats_by_company ;;
        8) get_quality_alerts ;;
        9) get_flagged_messages ;;
        10) trigger_alert_check ;;
        r|R)
            get_credentials
            get_token
            ;;
        q|Q)
            echo -e "${CYAN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac

    echo -e "\n${WHITE}Press Enter to continue...${NC}"
    read
done
