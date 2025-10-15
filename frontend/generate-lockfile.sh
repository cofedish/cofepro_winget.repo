#!/bin/bash
# Script to generate package-lock.json
# Run this on a machine with npm installed

echo "Generating package-lock.json..."
rm -f package-lock.json
npm install --package-lock-only
echo "Done! package-lock.json created."
