#!/bin/bash
# Test runner script for nextcloud-ingestor

set -e

echo "Installing test dependencies..."
pip install -r requirements-test.txt

echo "Running Activity API tests..."
python -m pytest test/test_activity_api.py -v

echo "Running all tests..."
python -m pytest test/ -v