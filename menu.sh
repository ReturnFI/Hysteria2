#!/bin/bash

source /etc/hysteria/core/scripts/utils.sh

# OPTION HANDLERS (ONLY NEEDED ONE)

hysteria2_add_user_handler() {

}

hysteria2_remove_user_handler() {

}

hysteria2_show_user_uri_hanndler() {

}

hysteria2_change_port_handler() {

}


# Function to modify users
hysteria2_modify_users() {
    modify_script="/etc/hysteria/users/modify.py"
    github_raw_url="https://raw.githubusercontent.com/ReturnFI/Hysteria2/main/modify.py"

    [ -f "$modify_script" ] || wget "$github_raw_url" -O "$modify_script" >/dev/null 2>&1

    python3 "$modify_script"
}

warp_configure_handler() {

}


# Function to display the main menu
display_main_menu() {
    clear
    tput setaf 7 ; tput setab 4 ; tput bold ; printf '%40s%s%-12s\n' "◇───────────ㅤ🚀ㅤWelcome To Hysteria2 Managementㅤ🚀ㅤ───────────◇" ; tput sgr0
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${green}• OS: ${NC}$OS           ${green}• ARCH: ${NC}$ARCH"
    echo -e "${green}• ISP: ${NC}$ISP         ${green}• CPU: ${NC}$CPU"
    echo -e "${green}• IP: ${NC}$IP                ${green}• RAM: ${NC}$RAM"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${yellow}                   ☼ Main Menu ☼                   ${NC}"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${green}[1] ${NC}↝ Hysteria2 Menu"
    echo -e "${cyan}[2] ${NC}↝ Advance Menu"
    echo -e "${red}[0] ${NC}↝ Exit"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Function to handle main menu options
main_menu() {
    clear
    local choice
    while true; do
        get_system_info
        display_main_menu
        read -r choice
        case $choice in
            1) hysteria2_menu ;;
            2) advance_menu ;;
            0) exit 0 ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Function to display the Hysteria2 menu
display_hysteria2_menu() {
    clear
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${yellow}                   ☼ Hysteria2 Menu ☼                   ${NC}"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -e "${green}[1] ${NC}↝ Install and Configure Hysteria2"
    echo -e "${cyan}[2] ${NC}↝ Add User"
    echo -e "${cyan}[3] ${NC}↝ Modify User"
    echo -e "${cyan}[4] ${NC}↝ Show URI"
    echo -e "${cyan}[5] ${NC}↝ Check Traffic Status"
    echo -e "${cyan}[6] ${NC}↝ Remove User"

    echo -e "${red}[0] ${NC}↝ Back to Main Menu"

    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"

    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Function to handle Hysteria2 menu options
hysteria2_menu() {
    clear
    local choice
    while true; do
        get_system_info
        display_hysteria2_menu
        read -r choice
        case $choice in
            1) python3 /etc/hysteria/core/cli.py install-hysteria2 ;;
            2) hysteria2_add_user_handler ;;
            3) hysteria2_modify_users ;;
            4) hysteria2_show_user_uri_hanndler ;;
            5) python3 /etc/hysteria2/core/cli.py traffic_status ;;
            6) hysteria2_remove_user_handler ;;
            0) return ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Function to get Advance menu
display_advance_menu() {
    clear
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${yellow}                   ☼ Advance Menu ☼                   ${NC}"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -e "${green}[1] ${NC}↝ Install TCP Brutal"
    echo -e "${green}[2] ${NC}↝ Install WARP"
    echo -e "${cyan}[3] ${NC}↝ Configure WARP"
    echo -e "${red}[4] ${NC}↝ Uninstall WARP"
    echo -e "${cyan}[5] ${NC}↝ Change Port Hysteria2"
    echo -e "${cyan}[6] ${NC}↝ Update Core Hysteria2"
    echo -e "${red}[7] ${NC}↝ Uninstall Hysteria2"
    echo -e "${red}[0] ${NC}↝ Back to Main Menu"
    echo -e "${LPurple}◇──────────────────────────────────────────────────────────────────────◇${NC}"
    echo -ne "${yellow}➜ Enter your option: ${NC}"
}

# Function to handle Advance menu options
advance_menu() {
    clear
    local choice
    while true; do
        display_advance_menu
        read -r choice
        case $choice in
            1) python3 /etc/hysteria/core/cli.py install-tcp-brutal ;;
            2) python3 /etc/hysteria/core/cli.py install-warp ;;
            3) warp_configure_handler ;;
            4) python3 /etc/hysteria/core/cli.py uninstall-warp ;;
            5) hysteria2_change_port_handler ;;
            6) python3 /etc/hysteria/core/cli.py update-hysteria2 ;;
            7) python3 /etc/hysteria/core/cli.py uninstall-hysteria2 ;;
            0) return ;;
            *) echo "Invalid option. Please try again." ;;
        esac
        echo
        read -rp "Press Enter to continue..."
    done
}

# Main function to run the script
main() {
    main_menu
}

define_colors
# Run the main function
main
