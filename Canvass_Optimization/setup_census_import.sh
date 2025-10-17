#!/bin/bash

# Canvass Optimization Census Import Setup Script
# ===============================================
# 
# This script sets up the complete environment for census data import
# and canvass optimization analysis for Forsyth County, NC
#
# Usage:
#   chmod +x setup_census_import.sh
#   ./setup_census_import.sh

set -e  # Exit on any error

echo "🚀 Setting up Canvass Optimization Census Import Environment"
echo "============================================================"

# Configuration
VENV_NAME="canvass_env"
PYTHON_MIN_VERSION="3.8"
PROJECT_DIR=$(pwd)
CONFIG_FILE="census_config.ini"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Found Python $PYTHON_VERSION"
    
    # Simple version check (assumes format like 3.8, 3.9, etc.)
    if [[ $(echo "$PYTHON_VERSION < $PYTHON_MIN_VERSION" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
        print_error "Python $PYTHON_MIN_VERSION or higher is required. Found $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python version check passed"
}

# Create virtual environment
setup_virtual_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ -d "$VENV_NAME" ]; then
        print_warning "Virtual environment '$VENV_NAME' already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_NAME"
            print_status "Removed existing virtual environment"
        else
            print_status "Using existing virtual environment"
            return 0
        fi
    fi
    
    python3 -m venv "$VENV_NAME"
    print_success "Virtual environment created: $VENV_NAME"
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed from requirements.txt"
    else
        print_warning "requirements.txt not found, installing core dependencies manually"
        pip install sqlalchemy geoalchemy2 psycopg2-binary requests shapely fiona click
    fi
}

# Check for PostgreSQL and PostGIS
check_postgresql() {
    print_status "Checking PostgreSQL installation..."
    
    if command -v psql &> /dev/null; then
        PSQL_VERSION=$(psql --version | head -n1 | awk '{print $3}')
        print_success "Found PostgreSQL: $PSQL_VERSION"
        
        # Check if PostGIS is available (this is a basic check)
        if command -v shp2pgsql &> /dev/null; then
            print_success "PostGIS tools found"
        else
            print_warning "PostGIS tools not found. Install with: sudo apt-get install postgis"
        fi
    else
        print_warning "PostgreSQL not found. For full functionality, install with:"
        echo "    Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib postgis"
        echo "    macOS: brew install postgresql postgis"
        echo "    Or use SQLite for local development"
    fi
}

# Create database (PostgreSQL)
create_database() {
    if command -v psql &> /dev/null; then
        print_status "Setting up PostgreSQL database..."
        
        DB_NAME="canvass_optimization"
        DB_USER="postgres"
        
        read -p "Create PostgreSQL database '$DB_NAME'? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Note: This assumes PostgreSQL is running and user has access
            createdb -U "$DB_USER" "$DB_NAME" 2>/dev/null || print_warning "Database may already exist"
            psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null || print_warning "PostGIS extension setup may have failed"
            print_success "Database setup attempted (check PostgreSQL logs for any issues)"
        fi
    fi
}

# Set up configuration file
setup_configuration() {
    print_status "Setting up configuration file..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file '$CONFIG_FILE' not found!"
        print_status "Please ensure census_config.ini exists in the project directory"
        return 1
    fi
    
    # Check if API key is set
    if grep -q "YOUR_CENSUS_API_KEY_HERE" "$CONFIG_FILE"; then
        print_warning "Census API key not configured!"
        echo ""
        echo "To get a free Census API key:"
        echo "1. Visit: https://api.census.gov/data/key_signup.html"
        echo "2. Sign up for an API key"
        echo "3. Edit $CONFIG_FILE and replace 'YOUR_CENSUS_API_KEY_HERE' with your key"
        echo ""
        read -p "Do you have a Census API key to enter now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter your Census API key: " API_KEY
            sed -i.bak "s/YOUR_CENSUS_API_KEY_HERE/$API_KEY/" "$CONFIG_FILE"
            print_success "API key updated in configuration"
        fi
    else
        print_success "Configuration file looks good"
    fi
}

# Create sample data directory
create_directories() {
    print_status "Creating project directories..."
    
    mkdir -p data/raw
    mkdir -p data/processed
    mkdir -p logs
    mkdir -p tiger_downloads
    mkdir -p tiger_extracted
    mkdir -p exports
    
    print_success "Project directories created"
}

# Test the installation
test_installation() {
    print_status "Testing installation..."
    
    source "$VENV_NAME/bin/activate"
    
    # Test simple census processor
    if [ -f "simple_census_processor.py" ]; then
        python simple_census_processor.py --help > /dev/null
        print_success "Simple census processor test passed"
    fi
    
    # Test main census importer
    if [ -f "census_data_importer.py" ]; then
        python census_data_importer.py --help > /dev/null
        print_success "Census data importer test passed"
    fi
    
    print_success "Installation test completed"
}

# Main setup process
main() {
    echo "Starting setup process..."
    echo ""
    
    check_python_version
    setup_virtual_environment
    install_dependencies
    check_postgresql
    create_database
    setup_configuration
    create_directories
    test_installation
    
    echo ""
    print_success "Setup completed successfully! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   source $VENV_NAME/bin/activate"
    echo ""
    echo "2. Configure your Census API key in $CONFIG_FILE (if not done already)"
    echo ""
    echo "3. Test the simple processor:"
    echo "   python simple_census_processor.py --state 37 --county 067 --format report"
    echo ""
    echo "4. Run full census import:"
    echo "   python census_data_importer.py --config $CONFIG_FILE"
    echo ""
    echo "5. Open the HTML maps in your browser:"
    echo "   - forsyth_precinct_704_map.html"
    echo "   - forsyth_precincts_census_intersection.html"
    echo ""
}

# Run main function
main "$@"