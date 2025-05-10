#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[1;94m'
NC='\033[0m'
BOLD='\033[1m'

CHECK_MARK="[✓]"
CROSS_MARK="[✗]"
INFO_MARK="[i]"
WARNING_MARK="[!]"

log_info() {
    echo -e "${BLUE}${INFO_MARK} ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}${CHECK_MARK} ${1}${NC}"
}

log_warning() {
    echo -e "${YELLOW}${WARNING_MARK} ${1}${NC}"
}

log_error() {
    echo -e "${RED}${CROSS_MARK} ${1}${NC}" >&2
}

handle_error() {
    log_error "Error occurred at line $1"
    exit 1
}

trap 'handle_error $LINENO' ERR

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This script must be run as root."
        exit 1
    fi
    log_info "Running with root privileges"
}

install_bc_if_needed() {
    if ! command -v bc &> /dev/null; then
        log_info "Installing bc package..."
        
        if command -v apt &> /dev/null; then
            apt update -qq &> /dev/null && apt install -y -qq bc &> /dev/null
        elif command -v dnf &> /dev/null; then
            dnf install -y -q bc &> /dev/null
        fi
        
        if [ $? -ne 0 ]; then
            log_error "Failed to install bc package."
            exit 1
        fi
        log_success "Installed bc package"
    fi
}

check_os_version() {
    local os_name os_version

    log_info "Checking OS compatibility..."
    
    install_bc_if_needed
    
    if [ -f /etc/os-release ]; then
        os_name=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
        os_version=$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
    else
        log_error "Unsupported OS or unable to determine OS version."
        exit 1
    fi

    if [[ "$os_name" == "ubuntu" && $(echo "$os_version >= 22" | bc) -eq 1 ]] ||
       [[ "$os_name" == "debian" && $(echo "$os_version >= 12" | bc) -eq 1 ]] ||
       [[ "$os_name" == "rocky" && $(echo "$os_version >= 9" | bc) -eq 1 ]] ||
       [[ "$os_name" == "almalinux" && $(echo "$os_version >= 9" | bc) -eq 1 ]]; then
        log_success "OS check passed: $os_name $os_version"
        export OS_TYPE="$os_name"
        return 0
    else
        log_error "This script is only supported on Ubuntu 22+, Debian 12+, Rocky Linux 9+, or AlmaLinux 9+."
        exit 1
    fi
}

install_packages() {
    local DEBIAN_PACKAGES=("jq" "qrencode" "curl" "pwgen" "python3" "python3-pip" "python3-venv" "git" "bc" "zip" "cron" "lsof")
    local RHEL_PACKAGES=("jq" "qrencode" "curl" "pwgen" "python3" "python3-pip" "git" "bc" "zip" "cronie" "lsof")
    local REQUIRED_PACKAGES=()
    local MISSING_PACKAGES=()
    
    log_info "Checking required packages..."
    
    if [[ "$OS_TYPE" == "ubuntu" || "$OS_TYPE" == "debian" ]]; then
        REQUIRED_PACKAGES=("${DEBIAN_PACKAGES[@]}")
        PKG_MANAGER="apt"
        UPDATE_CMD="apt update -qq"
        UPGRADE_CMD="apt upgrade -y -qq"
        INSTALL_CMD="apt install -y -qq"
    else 
        REQUIRED_PACKAGES=("${RHEL_PACKAGES[@]}")
        PKG_MANAGER="dnf"
        UPDATE_CMD="dnf check-update -q"
        UPGRADE_CMD="dnf upgrade -y -q"
        INSTALL_CMD="dnf install -y -q"
    fi
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! command -v "$package" &> /dev/null && ! rpm -q "$package" &> /dev/null 2>&1; then
            MISSING_PACKAGES+=("$package")
        else
            log_success "Package $package is already installed"
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
        log_info "Installing missing packages: ${MISSING_PACKAGES[*]}"
        eval "$UPDATE_CMD" &> /dev/null || { log_error "Failed to update package repositories"; exit 1; }
        eval "$UPGRADE_CMD" &> /dev/null || { log_warning "Failed to upgrade packages, continuing..."; }
        
        for package in "${MISSING_PACKAGES[@]}"; do
            log_info "Installing $package..."
            if eval "$INSTALL_CMD $package" &> /dev/null; then
                log_success "Installed $package"
            else
                log_error "Failed to install $package"
                exit 1
            fi
        done
    else
        log_success "All required packages are already installed."
    fi
}

setup_python() {
    log_info "Setting up Python 3.12 or 3.10+ environment..."
    
    if [[ "$OS_TYPE" == "ubuntu" || "$OS_TYPE" == "debian" ]]; then
        if ! command -v add-apt-repository &> /dev/null; then
            apt install -y -qq software-properties-common &> /dev/null
        fi
        
        if [[ "$OS_TYPE" == "ubuntu" ]]; then
            log_info "Adding deadsnakes PPA for Python 3.12..."
            add-apt-repository -y ppa:deadsnakes/ppa &> /dev/null || log_warning "Could not add deadsnakes PPA, will try system Python"
            apt update -qq &> /dev/null
            apt install -y -qq python3.12 python3.12-venv python3.12-dev &> /dev/null || log_warning "Could not install Python 3.12, will check for 3.10+"
        fi
    elif [[ "$OS_TYPE" == "rocky" || "$OS_TYPE" == "almalinux" ]]; then
        log_info "Enabling additional repositories for Python 3.12..."
        dnf install -y -q epel-release &> /dev/null
        dnf config-manager --set-enabled crb &> /dev/null || dnf config-manager --set-enabled powertools &> /dev/null || log_warning "Could not enable CRB/PowerTools repo"
        
        # Try to install Python 3.12 from EPEL if available
        dnf install -y -q python3.12 &> /dev/null || log_warning "Could not install Python 3.12, will check for 3.10+"
    fi
    
    if command -v python3.12 &> /dev/null; then
        log_success "Python 3.12 is available"
        PYTHON_CMD="python3.12"
        PYTHON_VERSION="3.12"
    else
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d " " -f 2 | cut -d "." -f 1,2)
        
        if [ $(echo "$PYTHON_VERSION >= 3.10" | bc) -eq 1 ]; then
            log_success "Python $PYTHON_VERSION is available and meets minimum requirement (3.10+)"
            PYTHON_CMD="python3"
        else
            # Try to install Python 3.10 as fallback
            log_info "Python $PYTHON_VERSION does not meet minimum requirement. Attempting to install Python 3.10..."
            
            if [[ "$OS_TYPE" == "ubuntu" || "$OS_TYPE" == "debian" ]]; then
                apt install -y -qq python3.10 python3.10-venv python3.10-dev &> /dev/null && PYTHON_CMD="python3.10" && PYTHON_VERSION="3.10"
            elif [[ "$OS_TYPE" == "rocky" || "$OS_TYPE" == "almalinux" ]]; then
                dnf install -y -q python3.10 &> /dev/null && PYTHON_CMD="python3.10" && PYTHON_VERSION="3.10"
            fi
            
            if [ -z "$PYTHON_CMD" ]; then
                log_error "Failed to install Python 3.10 or higher. Please install Python 3.10+ manually."
                exit 1
            else
                log_success "Installed Python $PYTHON_VERSION"
            fi
        fi
    fi
    
    export PYTHON_CMD
    log_info "Using Python $PYTHON_VERSION for virtual environment"
}

clone_repository() {
    log_info "Cloning Blitz repository..."
    
    if [ -d "/etc/hysteria" ]; then
        log_warning "Directory /etc/hysteria already exists."
        read -p "Do you want to remove it and clone again? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf /etc/hysteria
        else
            log_info "Using existing directory."
            return 0
        fi
    fi
    
    if git clone https://github.com/ReturnFI/Blitz /etc/hysteria &> /dev/null; then
        log_success "Repository cloned successfully"
    else
        log_error "Failed to clone repository"
        exit 1
    fi
}

setup_python_env() {
    log_info "Setting up Python virtual environment with Python $PYTHON_VERSION..."
    
    cd /etc/hysteria || { log_error "Failed to change to /etc/hysteria directory"; exit 1; }
    
    if $PYTHON_CMD -m venv hysteria2_venv &> /dev/null; then
        log_success "Created Python virtual environment with Python $PYTHON_VERSION"
    else
        log_error "Failed to create Python virtual environment"
        exit 1
    fi
    
    source /etc/hysteria/hysteria2_venv/bin/activate || { log_error "Failed to activate virtual environment"; exit 1; }
    
    log_info "Upgrading pip in virtual environment..."
    if pip install --upgrade pip &> /dev/null; then
        log_success "Upgraded pip in virtual environment"
    else
        log_warning "Failed to upgrade pip, continuing anyway..."
    fi
    
    log_info "Installing Python requirements..."
    if pip install -r requirements.txt &> /dev/null; then
        log_success "Installed Python requirements"
    else
        log_error "Failed to install Python requirements"
        exit 1
    fi
}

add_alias() {
    log_info "Adding 'hys2' alias to .bashrc..."
    
    if ! grep -q "alias hys2='source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/menu.sh'" ~/.bashrc; then
        echo "alias hys2='source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/menu.sh'" >> ~/.bashrc
        log_success "Added 'hys2' alias to .bashrc"
    else
        log_info "Alias 'hys2' already exists in .bashrc"
    fi
}

run_menu() {
    log_info "Preparing to run menu..."
    
    cd /etc/hysteria || { log_error "Failed to change to /etc/hysteria directory"; exit 1; }
    chmod +x menu.sh || { log_error "Failed to make menu.sh executable"; exit 1; }
    
    log_info "Starting menu..."
    echo -e "\n${BOLD}${GREEN}======== Launching Blitz Menu ========${NC}\n"
    ./menu.sh
}

main() {
    echo -e "\n${BOLD}${BLUE}======== Blitz Setup Script ========${NC}\n"
    
    check_root
    check_os_version
    install_packages
    setup_python
    clone_repository
    setup_python_env
    add_alias
    
    source ~/.bashrc &> /dev/null || true
    
    echo -e "\n${YELLOW}Starting Blitz in 3 seconds...${NC}"
    sleep 3
    
    run_menu
}

main
