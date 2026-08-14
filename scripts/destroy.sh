#!/usr/bin/env bash
# ==============================================================================
# AWS 3-Tier Infrastructure Destruction & Teardown Script
# ==============================================================================
# DESCRIPTION:
#   This utility coordinates the teardown of the AWS 3-tier PHP CodeIgniter
#   infrastructure stack, ensuring safe and ordered removal of all provisioned
#   resources.
#
# REQUIREMENTS:
#   - OpenTofu CLI >= 1.6.0
#   - OpenTofu provider credentials (supported sources include AWS environment
#     variables, profiles, SSO, or IAM roles) and active access to the target
#     state backend.
#   - Initialized backend state directory (.terraform)
#
# USAGE:
#   ./scripts/destroy.sh
# ==============================================================================

# Exit immediately on errors, unset variables, or failed pipes
set -euo pipefail

# ANSI escape codes for colored log outputs
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0;3m' # No Color

# Print the starting warning header banner
echo -e "${RED}=== WARNING: Starting AWS 3-Tier Infrastructure Destruction ===${NC}"

# Check if OpenTofu CLI is installed and available in PATH
if ! command -v tofu &> /dev/null; then
    echo -e "${RED}[Error] OpenTofu (tofu) CLI is not installed.${NC}"
    echo "To install OpenTofu, please refer to: https://opentofu.org/docs/intro/install/"
    exit 1
fi

# Navigate to the terraform configuration folder relative to the script location
cd "$(dirname "$0")/../terraform"

# Verify OpenTofu state backend directory is initialized
if [ ! -d ".terraform" ]; then
    echo -e "${RED}[Error] OpenTofu is not initialized. Run deploy.sh first or run 'tofu init' in the terraform/ directory.${NC}"
    exit 1
fi

# Ask the operator for absolute, explicit deletion confirmation
read -p "Are you absolutely sure you want to completely DESTROY all deployed AWS resources? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Run destruction with auto-approve to clean up all cloud assets
    echo -e "${BLUE}Running tofu destroy...${NC}"
    tofu destroy -auto-approve
    echo -e "${RED}=== Infrastructure Destroyed! ===${NC}"
else
    # Cancel gracefully if user objects
    echo -e "${BLUE}Destruction cancelled by user.${NC}"
fi
