#!/bin/bash
# Environment loader script with PATH scoping

# Determine the environment based on current path or argument
determine_environment() {
    local env_arg="${1:-}"
    local current_path=$(pwd)
    
    # Check if environment is explicitly provided
    if [ -n "$env_arg" ]; then
        echo "$env_arg"
        return
    fi
    
    # Determine environment based on current path
    case "$current_path" in
        */environments/dev*|*/docker/dev*)
            echo "dev"
            ;;
        */environments/test*|*/docker/test*)
            echo "test"
            ;;
        */environments/staging*)
            echo "staging"
            ;;
        */environments/prod*|*/docker/prod*)
            echo "prod"
            ;;
        *)
            echo "dev" # Default to dev
            ;;
    esac
}

# Load environment-specific configuration
load_environment() {
    local environment=$(determine_environment "$1")
    local base_path="${2:-$(dirname "$(readlink -f "$0")")/../environments}"
    local env_path="$base_path/$environment"
    
    echo "Loading environment: $environment"
    echo "Environment path: $env_path"
    
    # Set environment variable
    export ENVIRONMENT="$environment"
    
    # Update PATH to include environment-specific binaries
    export PATH="$env_path/bin:$PATH"
    
    # Load main environment file
    if [ -f "$env_path/.env" ]; then
        echo "Loading $env_path/.env"
        set -a
        source "$env_path/.env"
        set +a
    else
        echo "Warning: $env_path/.env not found"
    fi
    
    # Load local overrides if they exist
    if [ -f "$env_path/.env.local" ]; then
        echo "Loading $env_path/.env.local"
        set -a
        source "$env_path/.env.local"
        set +a
    fi
    
    # Load database-specific environment if exists
    if [ -f "$env_path/.env.db" ]; then
        echo "Loading $env_path/.env.db"
        set -a
        source "$env_path/.env.db"
        set +a
    fi
    
    # Set Python path to include environment-specific modules
    export PYTHONPATH="$env_path/lib:$PYTHONPATH"
    
    # Set up environment-specific tool configurations
    export ANSIBLE_CONFIG="$env_path/ansible.cfg"
    export DOCKER_CONFIG="$env_path/.docker"
    export KUBECONFIG="$env_path/kubeconfig"
    
    echo "Environment loaded successfully!"
    echo "PATH: $PATH"
    echo "PYTHONPATH: $PYTHONPATH"
}

# Validate environment configuration
validate_environment() {
    local required_vars=(
        "APP_NAME"
        "ENVIRONMENT"
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "Error: Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        return 1
    fi
    
    echo "Environment validation passed!"
    return 0
}

# Main execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    load_environment "$@"
    validate_environment
fi