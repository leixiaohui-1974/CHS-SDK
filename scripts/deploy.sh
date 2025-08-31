#!/bin/bash

# CHS Simulation Platform Deployment Script
# This script automates the deployment process for different environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
NAMESPACE="chs-simulation"
IMAGE_TAG="latest"
DRY_RUN=false
VERBOSE=false
SKIP_BUILD=false
SKIP_TESTS=false

# Function to print colored output
print_info() {
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

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy CHS Simulation Platform to Kubernetes

Options:
    -e, --environment ENV    Target environment (development|staging|production) [default: development]
    -n, --namespace NS       Kubernetes namespace [default: chs-simulation]
    -t, --tag TAG           Docker image tag [default: latest]
    -d, --dry-run           Show what would be deployed without actually deploying
    -v, --verbose           Enable verbose output
    --skip-build            Skip Docker image build
    --skip-tests            Skip running tests
    -h, --help              Show this help message

Examples:
    $0 -e staging -t v1.2.3
    $0 --environment production --tag latest --dry-run
    $0 -e development --skip-build

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_error "Valid environments: development, staging, production"
    exit 1
fi

# Set namespace based on environment
if [[ "$ENVIRONMENT" == "staging" ]]; then
    NAMESPACE="chs-simulation-staging"
elif [[ "$ENVIRONMENT" == "production" ]]; then
    NAMESPACE="chs-simulation"
fi

print_info "Starting deployment for environment: $ENVIRONMENT"
print_info "Namespace: $NAMESPACE"
print_info "Image tag: $IMAGE_TAG"
print_info "Dry run: $DRY_RUN"

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if docker is installed (unless skipping build)
    if [[ "$SKIP_BUILD" == false ]] && ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        print_warning "Helm is not installed. Some features may not be available."
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    if [[ "$SKIP_BUILD" == true ]]; then
        print_info "Skipping Docker image build"
        return
    fi
    
    print_info "Building Docker images..."
    
    # Build the main application image
    docker build -t "ghcr.io/your-org/chs-sdk:$IMAGE_TAG" .
    
    if [[ "$ENVIRONMENT" != "development" ]]; then
        print_info "Pushing image to registry..."
        docker push "ghcr.io/your-org/chs-sdk:$IMAGE_TAG"
    fi
    
    print_success "Docker images built successfully"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == true ]]; then
        print_info "Skipping tests"
        return
    fi
    
    print_info "Running tests..."
    
    # Run frontend tests
    print_info "Running frontend tests..."
    cd frontend
    npm ci
    npm run test:unit
    npm run lint
    cd ..
    
    # Run backend tests
    print_info "Running backend tests..."
    cd api
    pip install -r requirements.txt
    python -m pytest tests/ -v
    cd ..
    
    print_success "All tests passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    print_info "Creating namespace if it doesn't exist..."
    
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would create namespace: $NAMESPACE"
        return
    fi
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    print_success "Namespace $NAMESPACE is ready"
}

# Deploy secrets and configmaps
deploy_config() {
    print_info "Deploying configuration..."
    
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would deploy configuration to namespace: $NAMESPACE"
        kubectl apply -f k8s/configmap.yaml --namespace="$NAMESPACE" --dry-run=client
        return
    fi
    
    # Apply configmaps and secrets
    kubectl apply -f k8s/configmap.yaml --namespace="$NAMESPACE"
    
    print_success "Configuration deployed"
}

# Deploy storage
deploy_storage() {
    print_info "Deploying storage..."
    
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would deploy storage to namespace: $NAMESPACE"
        kubectl apply -f k8s/storage.yaml --namespace="$NAMESPACE" --dry-run=client
        return
    fi
    
    kubectl apply -f k8s/storage.yaml --namespace="$NAMESPACE"
    
    print_success "Storage deployed"
}

# Deploy applications
deploy_applications() {
    print_info "Deploying applications..."
    
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would deploy applications to namespace: $NAMESPACE"
        kubectl apply -f k8s/deployment.yaml --namespace="$NAMESPACE" --dry-run=client
        kubectl apply -f k8s/service.yaml --namespace="$NAMESPACE" --dry-run=client
        return
    fi
    
    # Update image tags in deployment
    sed -i.bak "s|ghcr.io/your-org/chs-sdk:.*|ghcr.io/your-org/chs-sdk:$IMAGE_TAG|g" k8s/deployment.yaml
    
    # Apply deployments and services
    kubectl apply -f k8s/deployment.yaml --namespace="$NAMESPACE"
    kubectl apply -f k8s/service.yaml --namespace="$NAMESPACE"
    
    # Restore original deployment file
    mv k8s/deployment.yaml.bak k8s/deployment.yaml
    
    print_success "Applications deployed"
}

# Deploy ingress
deploy_ingress() {
    if [[ "$ENVIRONMENT" == "development" ]]; then
        print_info "Skipping ingress deployment for development environment"
        return
    fi
    
    print_info "Deploying ingress..."
    
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would deploy ingress to namespace: $NAMESPACE"
        kubectl apply -f k8s/ingress.yaml --namespace="$NAMESPACE" --dry-run=client
        return
    fi
    
    kubectl apply -f k8s/ingress.yaml --namespace="$NAMESPACE"
    
    print_success "Ingress deployed"
}

# Wait for deployments to be ready
wait_for_deployments() {
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would wait for deployments to be ready"
        return
    fi
    
    print_info "Waiting for deployments to be ready..."
    
    # Wait for API deployment
    kubectl rollout status deployment/chs-simulation-api --namespace="$NAMESPACE" --timeout=300s
    
    # Wait for frontend deployment (if not development)
    if [[ "$ENVIRONMENT" != "development" ]]; then
        kubectl rollout status deployment/chs-simulation-frontend --namespace="$NAMESPACE" --timeout=300s
    fi
    
    # Wait for database deployment
    kubectl rollout status deployment/postgres --namespace="$NAMESPACE" --timeout=300s
    
    # Wait for redis deployment
    kubectl rollout status deployment/redis --namespace="$NAMESPACE" --timeout=300s
    
    print_success "All deployments are ready"
}

# Run database migrations
run_migrations() {
    if [[ "$DRY_RUN" == true ]]; then
        print_info "[DRY RUN] Would run database migrations"
        return
    fi
    
    print_info "Running database migrations..."
    
    # Get the first API pod
    API_POD=$(kubectl get pods --namespace="$NAMESPACE" -l app=chs-simulation-api -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -z "$API_POD" ]]; then
        print_error "No API pods found"
        exit 1
    fi
    
    # Run migrations
    kubectl exec "$API_POD" --namespace="$NAMESPACE" -- python -m alembic upgrade head
    
    print_success "Database migrations completed"
}

# Show deployment status
show_status() {
    print_info "Deployment status:"
    
    echo
    print_info "Pods:"
    kubectl get pods --namespace="$NAMESPACE" -o wide
    
    echo
    print_info "Services:"
    kubectl get services --namespace="$NAMESPACE"
    
    if [[ "$ENVIRONMENT" != "development" ]]; then
        echo
        print_info "Ingress:"
        kubectl get ingress --namespace="$NAMESPACE"
    fi
    
    echo
    print_info "Persistent Volume Claims:"
    kubectl get pvc --namespace="$NAMESPACE"
}

# Cleanup function
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Deployment failed!"
        exit 1
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment flow
main() {
    print_info "Starting CHS Simulation Platform deployment..."
    
    check_prerequisites
    
    if [[ "$ENVIRONMENT" != "development" ]]; then
        build_images
    fi
    
    run_tests
    create_namespace
    deploy_config
    deploy_storage
    deploy_applications
    deploy_ingress
    wait_for_deployments
    run_migrations
    
    print_success "Deployment completed successfully!"
    
    show_status
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        print_info "For development, you can access the application at:"
        print_info "API: kubectl port-forward service/chs-simulation-api-service 8000:8000 --namespace=$NAMESPACE"
        print_info "Frontend: kubectl port-forward service/chs-simulation-frontend-service 3000:80 --namespace=$NAMESPACE"
    else
        print_info "Application should be available at the configured ingress URLs"
    fi
}

# Run main function
main