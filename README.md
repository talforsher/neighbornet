# NeighborNet Static Site

This repository contains the static version of the NeighborNet website, deployed to GitHub Pages.

## Site Structure

- `export/` - Static site files for deployment
- `site-static/` - Alternative static site structure
- `current-site/` - Latest downloaded static site

## Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the main branch.

## Local Development

To run the site locally:

```bash
# Using Python's built-in server
cd export
python3 -m http.server 8000

# Or using Node.js
npx serve export
```

## Adding New Content

1. Add new HTML files to the appropriate directory
2. Update navigation links in existing pages
3. Commit and push changes to trigger deployment

## Custom Domain

The site uses a custom domain (neighbornet.co.il) configured via CNAME file.
