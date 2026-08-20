#!/bin/bash

# AHOS Run Script for Linux/macOS
# Usage: ./run_ahos.sh [command] [options]

COMMAND=${1:-help}
shift

case $COMMAND in
    "api")
        echo "🚀 Starting AHOS API server..."
        echo "   Access the API at: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        uvicorn ahos.interfaces.api.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    "cli")
        echo "🚀 Starting AHOS CLI..."
        echo "   Type 'help' for available commands"
        echo ""
        python -m ahos.interfaces.cli.commands "$@"
        ;;
    "worker")
        echo "🚀 Starting AHOS Celery worker..."
        celery -A ahos.worker.celery_app worker --loglevel=info
        ;;
    "flower")
        echo "🚀 Starting Flower (Celery monitoring)..."
        echo "   Access Flower at: http://localhost:5555"
        celery -A ahos.worker.celery_app flower --port=5555
        ;;
    "docker")
        echo "🚀 Starting AHOS with Docker..."
        docker-compose up -d
        echo ""
        echo "Services started:"
        echo "  - API: http://localhost:8000"
        echo "  - Flower: http://localhost:5555"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - Redis: localhost:6379"
        ;;
    "test")
        echo "🧪 Running AHOS tests..."
        pytest tests/ -v
        ;;
    "setup")
        echo "🛠️  Running AHOS setup..."
        ./setup_ahos.sh
        ;;
    *)
        echo "AHOS - Artificial Hybrid Opportunity Scoring System"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  api         - Start the API server"
        echo "  cli         - Start the CLI interface"
        echo "  worker      - Start the Celery worker"
        echo "  flower      - Start Flower (Celery monitoring)"
        echo "  docker      - Start with Docker"
        echo "  test        - Run tests"
        echo "  setup       - Run setup script"
        echo "  help        - Show this help"
        ;;
esac
