# Deployment Guide

## GitHub Pages Setup

This guide will help you deploy the GFS Wave Forecast visualization to GitHub Pages.

### Prerequisites

- GitHub repository with this code
- Admin access to the repository

### Step-by-Step Instructions

#### 1. Enable GitHub Pages

1. Navigate to your repository on GitHub
2. Click on **Settings** (top menu)
3. Scroll down to **Pages** in the left sidebar
4. Under "Build and deployment":
   - **Source**: Select **GitHub Actions** (NOT "Deploy from a branch")
5. Click **Save** if prompted

#### 2. Trigger Deployment

The deployment will automatically trigger when you:
- Push to `main` or `master` branch
- Manually trigger via Actions tab

**To manually trigger:**
1. Go to **Actions** tab
2. Select **Deploy to GitHub Pages** workflow
3. Click **Run workflow** → **Run workflow**

#### 3. Wait for Deployment

The workflow takes about 1-2 minutes:
1. ✅ Checkout code
2. ✅ Install Python dependencies
3. ✅ Attempt to fetch real GFS data (may fail, that's OK)
4. ✅ Prepare files for deployment
5. ✅ Deploy to GitHub Pages

#### 4. View Your Site

Once deployment completes (green checkmark):
- Your site will be live at: `https://[your-username].github.io/GFS_Wave_Forecast/`
- The link also appears in the Actions workflow output

### Verification

Visit your deployed site and verify:
- [ ] Map loads correctly
- [ ] Wave vectors are visible
- [ ] Particle animation is running
- [ ] Time slider works
- [ ] Play/pause buttons function
- [ ] Clicking on map shows wave data

### Troubleshooting

**Deployment fails:**
- Check Actions tab for error details
- Ensure repository is public (or Pages is enabled for private repos)
- Verify workflow file is in `.github/workflows/deploy.yml`

**Site shows 404:**
- Wait a few minutes after deployment
- Check Settings → Pages shows the correct URL
- Verify "GitHub Actions" is selected as source

**Map doesn't load:**
- Check browser console (F12) for errors
- Ensure all files were deployed (check Actions artifacts)
- Try clearing browser cache

**No wave data:**
- The deployed version uses sample data (this is expected)
- For real data, run locally with `python backend/fetch_gfs_data.py`

### Custom Domain (Optional)

To use a custom domain:
1. Go to Settings → Pages
2. Add your custom domain under "Custom domain"
3. Update DNS records at your domain provider
4. Wait for DNS propagation (can take up to 24 hours)

### Updating the Deployment

Any push to `main`/`master` will automatically redeploy:

```bash
git add .
git commit -m "Update visualization"
git push origin main
```

The site will update within 1-2 minutes.

### Performance Tips

For the deployed version:
- Sample data is lightweight and loads instantly
- No external API calls required
- Works entirely client-side
- Can be used offline after initial load

### Security

- No API keys needed for GitHub Pages deployment
- All data is public (sample wave data)
- HTTPS enabled by default on GitHub Pages
- No server-side code execution

## Alternative Deployment Options

### Netlify

1. Go to [netlify.com](https://netlify.com)
2. Drag and drop your project folder
3. Done! Site is live

### Vercel

1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Deploy with one click

### Local Server

For development:
```bash
python backend/simple_server.py
# Visit http://localhost:8000
```

## Support

If you encounter issues:
1. Check the [README.md](README.md) troubleshooting section
2. Review Actions workflow logs
3. Open an issue on GitHub
