source /etc/hysteria/core/scripts/utils.sh
source /etc/hysteria/core/scripts/path.sh

check_warp_configuration() {
    echo "--------------------------------"
    echo -e "${LPurple}Current WARP Configuration: ${NC}"

    if jq -e '.acl.inline[]? | select(test("warps\\(all\\)"))' "$CONFIG_FILE" > /dev/null; then
        echo -e "${cyan}All traffic:${NC} ${green}Active${NC}"
    else
        echo -e "${cyan}All traffic:${NC} ${red}Inactive${NC}"
    fi

    if jq -e '.acl.inline[]? | select(test("warps\\(geosite:google\\)")) or select(test("warps\\(geoip:google\\)")) or select(test("warps\\(geosite:netflix\\)")) or select(test("warps\\(geosite:spotify\\)")) or select(test("warps\\(geosite:openai\\)")) or select(test("warps\\(geoip:openai\\)"))' "$CONFIG_FILE" > /dev/null; then
        echo -e "${cyan}Popular sites (Google, Netflix, etc.):${NC} ${green}Active${NC}"
    else
        echo -e "${cyan}Popular sites (Google, Netflix, etc.):${NC} ${red}Inactive${NC}"
    fi

    if jq -e '.acl.inline[]? | select(test("warps\\(geosite:ir\\)")) or select(test("warps\\(geoip:ir\\)"))' "$CONFIG_FILE" > /dev/null; then
        echo -e "${cyan}Domestic sites (geosite:ir, geoip:ir):${NC} ${green}Active${NC}"
    else
        echo -e "${cyan}Domestic sites (geosite:ir, geoip:ir):${NC} ${red}Inactive${NC}"
    fi

    if jq -e '.acl.inline[]? | select(test("reject\\(geosite:category-porn\\)"))' "$CONFIG_FILE" > /dev/null; then
        echo -e "${cyan}Block adult content:${NC} ${green}Active${NC}"
    else
        echo -e "${cyan}Block adult content:${NC} ${red}Inactive${NC}"
    fi
    echo "--------------------------------"
}
define_colors
check_warp_configuration
