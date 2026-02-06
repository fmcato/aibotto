#!/bin/bash

# AIBOTTO Docker Run Script
# This script runs the AIBOTTO project using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        print_error "Visit https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        print_error "Visit https://docs.docker.com/compose/install/"
        exit 1
    fi

    print_status "Docker and Docker Compose are installed"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_error "Please create a .env file with your configuration."
        print_error "You can copy .env.example to .env as a template:"
        print_error "  cp .env.example .env"
        print_error ""
        print_error "Required environment variables:"
        print_error "  - TELEGRAM_TOKEN (from @BotFather)"
        print_error "  - OPENAI_API_KEY (from OpenAI or compatible provider)"
        exit 1
    fi

    # Check if required environment variables are set
    source .env
    missing_vars=()

    if [ -z "$TELEGRAM_TOKEN" ]; then
        missing_vars+=("TELEGRAM_TOKEN")
    fi

    if [ -z "$OPENAI_API_KEY" ]; then
        missing_vars+=("OPENAI_API_KEY")
    fi

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_error "Please check your .env file"
        exit 1
    fi

    print_success ".env file is properly configured"
}

# Function to build and start the service
build_and_start() {
    print_status "Building Docker image..."
    docker-compose build
    
    print_status "Starting AIBOTTO..."
    docker-compose up -d
    
    print_success "AIBOTTO is now running in the background!"
}

# Function to show status
show_status() {
    print_status "Checking container status..."
    docker-compose ps
    
    print_status "Viewing logs (last 20 lines):"
    docker-compose logs --tail=20
}

# Function to stop the service
stop_service() {
    print_status "Stopping AIBOTTO..."
    docker-compose down
    
    print_success "AIBOTTO has been stopped"
}

# Function to show logs
show_logs() {
    if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
        print_status "Following logs (Ctrl+C to stop)..."
        docker-compose logs -f
    else
        print_status "Showing logs (last 50 lines)..."
        docker-compose logs --tail=50
    fi
}

# Function to restart the service
restart_service() {
    print_status "Restarting AIBOTTO..."
    docker-compose restart
    print_success "AIBOTTO has been restarted"
}

# Function to update and restart
update_restart() {
    print_status "Pulling latest changes..."
    git pull
    
    print_status "Rebuilding Docker image..."
    docker-compose build --no-cache
    
    print_status "Restarting AIBOTTO..."
    docker-compose up -d --force-recreate
    
    print_success "AIBOTTO has been updated and restarted!"
}

# Function to show help
show_help() {
    echo "AIBOTTO Docker Run Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Build and start the AIBOTTO service"
    echo "  stop      - Stop the AIBOTTO service"
    echo "  restart   - Restart the AIBOTTO service"
    echo "  status    - Show container status and recent logs"
    echo "  logs      - Show logs (last 50 lines)"
    echo "  logs -f   - Follow logs in real-time"
    echo "  update    - Pull latest changes, rebuild, and restart"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start the service"
    echo "  $0 logs -f   # Follow logs"
    echo "  $0 stop      # Stop the service"
}

# Main script logic
main() {
    case "${1:-start}" in
        start)
            check_docker
            check_env_file
            build_and_start
            show_status
            ;;
        stop)
            check_docker
            stop_service
            ;;
        restart)
            check_docker
            restart_service
            show_status
            ;;
        status)
            check_docker
            show_status
            ;;
        logs)
            check_docker
            show_logs "$2"
            ;;
        update)
            check_docker
            check_env_file
            update_restart
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"