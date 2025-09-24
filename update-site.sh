#!/bin/bash

# NeighborNet Static Site Update Script

echo "🔄 Updating NeighborNet static site..."

# Download the latest version of the site
echo "📥 Downloading latest site content..."
wget --recursive --no-clobber --page-requisites --html-extension --convert-links --restrict-file-names=windows --domains neighbornet.co.il --no-parent https://neighbornet.co.il/ -P ./latest-download/

# Copy to export directory for deployment
echo "📁 Copying to export directory..."
rm -rf export/*
cp -r latest-download/neighbornet.co.il/* export/

# Clean up
echo "🧹 Cleaning up..."
rm -rf latest-download/

echo "✅ Site updated successfully!"
echo "💡 Run 'git add . && git commit -m \"Update site\" && git push' to deploy"
