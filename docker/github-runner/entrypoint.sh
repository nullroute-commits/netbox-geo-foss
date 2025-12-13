#!/bin/bash
set -e

# Configure the runner
if [ -n "${GITHUB_ACCESS_TOKEN}" ] && [ -n "${ORGANIZATION}" ]; then
    # Organization runner
    ./config.sh --url https://github.com/${ORGANIZATION} \
        --token ${GITHUB_ACCESS_TOKEN} \
        --name ${RUNNER_NAME:-docker-runner} \
        --work ${RUNNER_WORKDIR:-_work} \
        --labels ${LABELS:-self-hosted,linux,x64,docker} \
        --unattended \
        --replace
elif [ -n "${GITHUB_ACCESS_TOKEN}" ] && [ -n "${REPO}" ]; then
    # Repository runner
    ./config.sh --url https://github.com/${REPO} \
        --token ${GITHUB_ACCESS_TOKEN} \
        --name ${RUNNER_NAME:-docker-runner} \
        --work ${RUNNER_WORKDIR:-_work} \
        --labels ${LABELS:-self-hosted,linux,x64,docker} \
        --unattended \
        --replace
else
    echo "Error: GITHUB_ACCESS_TOKEN and either ORGANIZATION or REPO must be set"
    exit 1
fi

# Run the runner
exec ./run.sh