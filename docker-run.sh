#!/bin/bash

# AIBOTTO Docker Run Script

set -e

start() {
    echo "🚀 Building Docker image..."
    docker compose build
    
    echo "🚀 Starting AIBOTTO..."
    docker compose up -d
    
    echo "✅ AIBOTTO is running!"
    echo "📋 Status:"
    docker compose ps
}

stop() {
    echo "🛑 Stopping AIBOTTO..."
    docker compose down
    echo "✅ AIBOTTO stopped"
}

restart() {
    echo "🔄 Restarting AIBOTTO..."
    docker compose restart
    echo "✅ AIBOTTO restarted"
}

logs() {
    if [ "$1" = "-f" ]; then
        echo "📝 Following logs (Ctrl+C to stop)..."
        docker compose logs -f
    else
        echo "📝 Recent logs:"
        docker compose logs --tail=20
    fi
}

status() {
    echo "📋 Container status:"
    docker compose ps
}

update() {
    echo "🔄 Pulling latest changes..."
    git pull
    
    echo "🔄 Rebuilding Docker image..."
    docker compose build --no-cache
    
    echo "🔄 Restarting AIBOTTO..."
    docker compose up -d --force-recreate
    
    echo "✅ AIBOTTO updated and restarted!"
}

help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Build and start the service"
    echo "  stop      - Stop the service"
    echo "  restart   - Restart the service"
    echo "  status    - Show container status"
    echo "  logs      - Show recent logs"
    echo "  logs -f   - Follow logs in real-time"
    echo "  update    - Update and restart"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs -f"
}

case "${1:-help}" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    logs) logs "$2" ;;
    update) update ;;
    help) help ;;
    *) echo "Unknown command: $1"; help; exit 1 ;;
esac