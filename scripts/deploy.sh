#!/usr/bin/env bash
# ==============================================================================
# AWS 3-Tier Infrastructure Deployment Script
# ==============================================================================
# DESCRIPTION:
#   This utility automates pre-flight validation, formatting, syntax checking,
#   and execution plan generation for deploying the secure AWS 3-Tier PHP stack
#   using OpenTofu.
#
# REQUIREMENTS:
#   - OpenTofu CLI >= 1.6.0 (or Terraform compatibility)
#   - AWS CLI configured with active credentials for the ap-southeast-5 region
#   - Access to the target state backend
#
# USAGE:
#   ./scripts/deploy.sh
# ==============================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# ANSI escape codes for colored log outputs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0;3m' # No Color

# Print the starting header banner
echo -e "${BLUE}=== Starting AWS 3-Tier Infrastructure Deployment ===${NC}"

# Check if OpenTofu CLI is installed and available in PATH
if ! command -v tofu &> /dev/null; then
    echo -e "${RED}[Error] OpenTofu (tofu) CLI is not installed.${NC}"
    echo "To install OpenTofu, please refer to: https://opentofu.org/docs/intro/install/"
    exit 1
fi

# Navigate to the terraform configuration folder relative to the script location
cd "$(dirname "$0")/../terraform"

# Ensure the required variables definition file (terraform.tfvars) exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${RED}[Warning] terraform.tfvars not found.${NC}"
    # If the template file is available, copy it to boot up standard settings
    if [ -f "terraform.tfvars.example" ]; then
        echo "Creating terraform.tfvars from terraform.tfvars.example..."
        cp terraform.tfvars.example terraform.tfvars
        echo -e "${GREEN}Created terraform.tfvars! Please review/update its contents before continuing.${NC}"
        exit 0
    else
        # Throw error if even the template is missing
        echo -e "${RED}[Error] terraform.tfvars.example missing!${NC}"
        exit 1
    fi
fi

# Run tofu init to download provider plugins and configure backend state
echo -e "${BLUE}Initializing OpenTofu...${NC}"
tofu init

# Run tofu fmt recursively to enforce clean and standardized HCL syntax formatting
echo -e "${BLUE}Formatting OpenTofu/HCL configs...${NC}"
tofu fmt -recursive

# Run tofu validate to check the syntax, wiring, and modules for static correctness
echo -e "${BLUE}Validating OpenTofu configs...${NC}"
tofu validate

# Generate a dry-run execution plan and serialize it to 'tfplan'
echo -e "${BLUE}Generating OpenTofu execution plan...${NC}"
tofu plan -out=tfplan

# Ask the operator for explicit deployment confirmation
read -p "Do you want to apply this deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Apply the generated execution plan if confirmed by user
    echo -e "${BLUE}Applying OpenTofu plan...${NC}"
    tofu apply tfplan
    echo -e "${GREEN}=== Deployment Complete! ===${NC}"
else
    # Cancel gracefully if user objects
    echo -e "${RED}Deployment cancelled by user.${NC}"
fi
