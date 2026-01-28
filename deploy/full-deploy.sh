#!/bin/bash
# ============================================================================
# Full Deployment Script for DocsAI on EC2 Ubuntu
# ============================================================================
# This script automates the complete deployment process from git clone onwards
# Usage:
#   HTTP-only:  sudo bash deploy/full-deploy.sh --http-only [--ip 34.201.10.84]
#   With SSL:   sudo bash deploy/full-deploy.sh --domain example.com --email admin@example.com
#   Interactive: sudo bash deploy/full-deploy.sh --interactive
# ============================================================================

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ubuntu/docsai"
ENV_FILE="${PROJECT_DIR}/.env.prod"
HTTP_ONLY=false
INTERACTIVE=false
DOMAIN=""
EMAIL=""
EC2_IP=""
SKIP_DB_SETUP=false
SKIP_SSL=false

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --http-only)
                HTTP_ONLY=true
                shift
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --ip)
                EC2_IP="$2"
                shift 2
                ;;
            --interactive)
                INTERACTIVE=true
                shift
                ;;
            --skip-db-setup)
                SKIP_DB_SETUP=true
                shift
                ;;
            --skip-ssl)
                SKIP_SSL=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Full Deployment Script for DocsAI on EC2 Ubuntu

Usage:
    sudo bash deploy/full-deploy.sh [OPTIONS]

Options:
    --http-only              Deploy with HTTP only (no SSL, IP-based)
    --domain DOMAIN         Domain name for SSL setup (e.g., example.com)
    --email EMAIL           Email for SSL certificate (e.g., admin@example.com)
    --ip IP                 EC2 IP address (default: auto-detect or prompt)
    --interactive           Interactive mode (prompts for all settings)
    --skip-db-setup         Skip database setup (use existing database)
    --skip-ssl              Skip SSL setup even if domain provided
    -h, --help              Show this help message

Examples:
    # HTTP-only deployment
    sudo bash deploy/full-deploy.sh --http-only --ip 34.201.10.84

    # SSL deployment with domain
    sudo bash deploy/full-deploy.sh --domain docsai.example.com --email admin@example.com

    # Interactive mode
    sudo bash deploy/full-deploy.sh --interactive

EOF
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory $PROJECT_DIR does not exist!"
        log_info "Please clone the repository first:"
        log_info "  git clone <repo-url> $PROJECT_DIR"
        exit 1
    fi
    
    # Check if manage.py exists
    if [ ! -f "$PROJECT_DIR/manage.py" ]; then
        log_error "manage.py not found in $PROJECT_DIR"
        log_error "Please ensure you're in the correct directory after git clone"
        exit 1
    fi
    
    # Check if deploy scripts exist
    if [ ! -f "$PROJECT_DIR/deploy/systemd/install-systemd.sh" ]; then
        log_error "Deployment scripts not found!"
        log_error "Please ensure all deploy scripts are present"
        exit 1
    fi
    
    log "Prerequisites check passed ✓"
}

# Get EC2 IP address
get_ec2_ip() {
    if [ -z "$EC2_IP" ]; then
        # Try to get public IP from metadata
        EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
        
        if [ -z "$EC2_IP" ]; then
            if [ "$INTERACTIVE" = true ]; then
                read -p "Enter EC2 IP address: " EC2_IP
            else
                log_warning "Could not auto-detect EC2 IP. Using 34.201.10.84 as default"
                EC2_IP="34.201.10.84"
            fi
        fi
    fi
    log_info "Using EC2 IP: $EC2_IP"
}

# Install system dependencies
install_system_dependencies() {
    log "Installing system dependencies..."
    
    apt update -qq
    apt install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        postgresql-client \
        postgresql \
        nginx \
        git \
        curl \
        wget \
        build-essential \
        libpq-dev \
        ufw \
        > /dev/null 2>&1
    
    # Install SSL tools if not HTTP-only
    if [ "$HTTP_ONLY" = false ] && [ "$SKIP_SSL" = false ]; then
        apt install -y certbot python3-certbot-nginx > /dev/null 2>&1
    fi
    
    log "System dependencies installed ✓"
}

# Setup PostgreSQL database
setup_database() {
    if [ "$SKIP_DB_SETUP" = true ]; then
        log_info "Skipping database setup (--skip-db-setup)"
        return
    fi
    
    log "Setting up PostgreSQL database..."
    
    if [ "$INTERACTIVE" = true ]; then
        read -p "Do you want to set up PostgreSQL on this EC2 instance? (y/n): " setup_local_db
        if [[ ! "$setup_local_db" =~ ^[Yy]$ ]]; then
            log_info "Skipping local database setup. Please configure RDS or external database."
            return
        fi
        
        read -p "Database name [docsai]: " db_name
        db_name=${db_name:-docsai}
        
        read -p "Database user [docsai_user]: " db_user
        db_user=${db_user:-docsai_user}
        
        read -sp "Database password: " db_password
        echo ""
    else
        # Default values
        db_name="docsai"
        db_user="docsai_user"
        db_password=$(openssl rand -base64 32)
        log_info "Generated random database password"
    fi
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE $db_name;" 2>/dev/null || log_warning "Database $db_name may already exist"
    sudo -u postgres psql -c "CREATE USER $db_user WITH PASSWORD '$db_password';" 2>/dev/null || log_warning "User $db_user may already exist"
    sudo -u postgres psql -c "ALTER ROLE $db_user SET client_encoding TO 'utf8';" 2>/dev/null || true
    sudo -u postgres psql -c "ALTER ROLE $db_user SET default_transaction_isolation TO 'read committed';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;" 2>/dev/null || true
    
    log "Database setup completed ✓"
    log_info "Database: $db_name"
    log_info "User: $db_user"
    if [ "$INTERACTIVE" = false ]; then
        log_info "Password: $db_password (save this securely!)"
    fi
}

# Setup Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log "Virtual environment created ✓"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate and upgrade pip
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel -q
    
    # Install requirements
    log "Installing Python dependencies (this may take a few minutes)..."
    pip install -r requirements.txt -q
    
    log "Python environment setup completed ✓"
}

# Generate Django secret key
generate_secret_key() {
    cd "$PROJECT_DIR"
    source venv/bin/activate
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
}

# Configure environment file
configure_environment() {
    log "Configuring environment file..."
    
    cd "$PROJECT_DIR"
    
    # Copy example if .env.prod doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.prod.example" ]; then
            cp .env.prod.example "$ENV_FILE"
            log "Created $ENV_FILE from template"
        else
            log_error ".env.prod.example not found!"
            exit 1
        fi
    else
        log_warning "$ENV_FILE already exists. Backing up..."
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Generate secret key if not set
    if ! grep -q "^SECRET_KEY=" "$ENV_FILE" || grep -q "^SECRET_KEY=$" "$ENV_FILE"; then
        secret_key=$(generate_secret_key)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=$secret_key|" "$ENV_FILE"
        else
            # Linux
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$secret_key|" "$ENV_FILE"
        fi
        log "Generated and set SECRET_KEY"
    fi
    
    # Set production environment
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^DJANGO_ENV=.*|DJANGO_ENV=production|" "$ENV_FILE"
        sed -i '' "s|^DEBUG=.*|DEBUG=False|" "$ENV_FILE"
    else
        sed -i "s|^DJANGO_ENV=.*|DJANGO_ENV=production|" "$ENV_FILE"
        sed -i "s|^DEBUG=.*|DEBUG=False|" "$ENV_FILE"
    fi
    
    # Set ALLOWED_HOSTS
    if [ -n "$DOMAIN" ]; then
        allowed_hosts="$DOMAIN,www.$DOMAIN,$EC2_IP,localhost,127.0.0.1"
    else
        allowed_hosts="$EC2_IP,localhost,127.0.0.1"
    fi
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$allowed_hosts|" "$ENV_FILE"
    else
        sed -i "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$allowed_hosts|" "$ENV_FILE"
    fi
    
    # Set file permissions
    chown ubuntu:ubuntu "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    
    log "Environment file configured ✓"
    
    if [ "$INTERACTIVE" = true ]; then
        log_info "Please review and edit $ENV_FILE with your database and other settings"
        read -p "Press Enter to continue after editing .env.prod..."
    else
        log_warning "Please review and update $ENV_FILE with your database credentials and other settings"
    fi
}

# Run Django migrations and setup
setup_django() {
    log "Setting up Django application..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    export DJANGO_ENV=production
    
    # Run migrations
    log "Running database migrations..."
    python manage.py migrate --noinput
    
    # Create logs directory
    mkdir -p logs
    chown ubuntu:ubuntu logs
    
    # Collect static files
    log "Collecting static files..."
    python manage.py collectstatic --noinput
    
    # Validate environment
    log "Validating environment..."
    python manage.py validate_env || log_warning "Environment validation had warnings"
    
    # Django check
    python manage.py check --deploy || log_warning "Django deployment check had warnings"
    
    log "Django setup completed ✓"
    
    # Prompt for superuser creation
    if [ "$INTERACTIVE" = true ]; then
        read -p "Do you want to create a superuser now? (y/n): " create_superuser
        if [[ "$create_superuser" =~ ^[Yy]$ ]]; then
            python manage.py createsuperuser
        fi
    else
        log_info "To create a superuser, run:"
        log_info "  cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser"
    fi
}

# Install Gunicorn systemd service
install_gunicorn() {
    log "Installing Gunicorn systemd service..."
    
    cd "$PROJECT_DIR"
    bash deploy/systemd/install-systemd.sh
    
    log "Gunicorn service installed ✓"
}

# Install Nginx configuration
install_nginx() {
    log "Installing Nginx configuration..."
    
    cd "$PROJECT_DIR"
    
    if [ "$HTTP_ONLY" = true ]; then
        bash deploy/nginx/install-nginx.sh --http-only
    else
        bash deploy/nginx/install-nginx.sh
        
        # Update server_name in config if domain provided
        if [ -n "$DOMAIN" ]; then
            nginx_config="/etc/nginx/sites-available/docsai.conf"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|server_name.*|server_name $DOMAIN www.$DOMAIN $EC2_IP;|g" "$nginx_config"
            else
                sed -i "s|server_name.*|server_name $DOMAIN www.$DOMAIN $EC2_IP;|g" "$nginx_config"
            fi
            systemctl reload nginx
        fi
    fi
    
    log "Nginx configuration installed ✓"
}

# Setup SSL certificate
setup_ssl() {
    if [ "$HTTP_ONLY" = true ] || [ "$SKIP_SSL" = true ]; then
        log_info "Skipping SSL setup"
        return
    fi
    
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        log_warning "Domain or email not provided. Skipping SSL setup"
        return
    fi
    
    log "Setting up SSL certificate..."
    
    cd "$PROJECT_DIR"
    bash deploy/ssl/setup-ssl.sh "$DOMAIN" "$EMAIL"
    
    log "SSL setup completed ✓"
}

# Install log rotation
install_logrotate() {
    log "Installing log rotation..."
    
    cd "$PROJECT_DIR"
    bash deploy/logrotate/install-logrotate.sh
    
    log "Log rotation installed ✓"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Allow SSH
    ufw allow OpenSSH > /dev/null 2>&1 || true
    
    # Allow HTTP/HTTPS
    if [ "$HTTP_ONLY" = true ]; then
        ufw allow 'Nginx HTTP' > /dev/null 2>&1 || true
    else
        ufw allow 'Nginx Full' > /dev/null 2>&1 || true
    fi
    
    # Enable firewall (non-interactive)
    echo "y" | ufw enable > /dev/null 2>&1 || true
    
    log "Firewall configured ✓"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check Gunicorn status
    if systemctl is-active --quiet gunicorn; then
        log "Gunicorn service is running ✓"
    else
        log_error "Gunicorn service is not running!"
        systemctl status gunicorn --no-pager || true
    fi
    
    # Check Nginx status
    if systemctl is-active --quiet nginx; then
        log "Nginx service is running ✓"
    else
        log_error "Nginx service is not running!"
        systemctl status nginx --no-pager || true
    fi
    
    # Test health endpoint
    sleep 2
    if [ "$HTTP_ONLY" = true ]; then
        health_url="http://$EC2_IP/api/v1/health/"
    else
        health_url="https://$DOMAIN/api/v1/health/"
    fi
    
    log_info "Testing health endpoint: $health_url"
    if curl -sf --connect-timeout 5 "$health_url" > /dev/null 2>&1; then
        log "Health check passed ✓"
    else
        log_warning "Health check failed. The application may still be starting up."
        log_info "Wait a few moments and try: curl $health_url"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Deployment Completed!${NC}"
    echo "=========================================="
    echo ""
    echo "Project Directory: $PROJECT_DIR"
    echo "Environment File: $ENV_FILE"
    echo ""
    
    if [ "$HTTP_ONLY" = true ]; then
        echo "Access URL: http://$EC2_IP"
        echo "Health Check: curl http://$EC2_IP/api/v1/health/"
    else
        echo "Access URL: https://$DOMAIN"
        echo "Health Check: curl https://$DOMAIN/api/v1/health/"
    fi
    
    echo ""
    echo "Useful Commands:"
    echo "  View Gunicorn logs: sudo journalctl -u gunicorn -f"
    echo "  View Nginx logs: sudo tail -f /var/log/nginx/docsai_error.log"
    echo "  Restart Gunicorn: sudo systemctl restart gunicorn"
    echo "  Reload Nginx: sudo systemctl reload nginx"
    echo "  Create superuser: cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser"
    echo ""
}

# Main deployment function
main() {
    echo ""
    echo "=========================================="
    echo "DocsAI Full Deployment Script"
    echo "=========================================="
    echo ""
    
    # Parse arguments
    parse_args "$@"
    
    # Get EC2 IP
    get_ec2_ip
    
    # Validate arguments
    if [ "$HTTP_ONLY" = false ] && [ -z "$DOMAIN" ] && [ "$INTERACTIVE" = false ]; then
        log_error "Either --http-only, --domain, or --interactive must be specified"
        show_help
        exit 1
    fi
    
    # Interactive mode prompts
    if [ "$INTERACTIVE" = true ]; then
        read -p "Deploy with HTTP only (no SSL)? (y/n): " http_only_choice
        if [[ "$http_only_choice" =~ ^[Yy]$ ]]; then
            HTTP_ONLY=true
        else
            read -p "Enter domain name: " DOMAIN
            read -p "Enter email for SSL certificate: " EMAIL
        fi
        
        read -p "Skip database setup? (y/n): " skip_db
        if [[ "$skip_db" =~ ^[Yy]$ ]]; then
            SKIP_DB_SETUP=true
        fi
    fi
    
    # Check root
    check_root
    
    # Run deployment steps
    check_prerequisites
    install_system_dependencies
    setup_database
    setup_python_env
    configure_environment
    setup_django
    install_gunicorn
    install_nginx
    setup_ssl
    install_logrotate
    configure_firewall
    verify_deployment
    print_summary
    
    log "Deployment script completed successfully!"
}

# Run main function
main "$@"
