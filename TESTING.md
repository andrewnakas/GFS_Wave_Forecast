# Quick Test Instructions

## Test Locally (Easiest - Works Right Now!)

### Method 1: Python Server (Recommended)
```bash
cd /home/user/GFS_Wave_Forecast
python3 backend/simple_server.py
```
Then open: http://localhost:8000

### Method 2: Direct File Open
Simply open `test.html` directly in your browser - it should work!

## Debug GitHub Pages 404 Issue

If you're getting a 404 on GitHub Pages, here are the steps to debug:

### Step 1: Check if Actions Ran
1. Go to: https://github.com/andrewnakas/GFS_Wave_Forecast/actions
2. Look for "Deploy to GitHub Pages" workflow
3. Check if it has a ✅ green checkmark or ❌ red X
4. Click on the latest run to see logs

### Step 2: Verify GitHub Pages Settings
1. Go to: https://github.com/andrewnakas/GFS_Wave_Forecast/settings/pages
2. Verify:
   - Source: "GitHub Actions" is selected
   - NOT "Deploy from a branch"
3. Screenshot what you see if unsure

### Step 3: Check Which Branch Deployed
The workflow is set to deploy from:
- main
- master
- claude/gfs-wave-current-forecast-011CUvvhwdZcCKGFDNJBhjsv

**Issue**: GitHub Pages might be looking for deployment from `main`, but we're on the feature branch.

### Step 4: Solution Options

**Option A: Merge to Main (Recommended)**
1. Create PR from feature branch to main
2. Merge it
3. Workflow will auto-deploy from main
4. Pages will work at: https://andrewnakas.github.io/GFS_Wave_Forecast/

**Option B: Force Deploy from Feature Branch**
1. Go to Actions tab
2. Click "Deploy to GitHub Pages"
3. Click "Run workflow"
4. Select branch: claude/gfs-wave-current-forecast-011CUvvhwdZcCKGFDNJBhjsv
5. Click "Run workflow"
6. Wait 2 minutes

**Option C: Test Locally Now**
Just run the Python server and test locally while we debug GitHub Pages.

## Common Issues

### "The source branch does not match"
- This means Pages is configured for a different branch
- Solution: Ensure "GitHub Actions" is selected (not branch deployment)

### "Workflow doesn't run"
- Check that workflow file is on the branch
- Manually trigger it from Actions tab

### "Deployment succeeds but still 404"
- Wait 5-10 minutes (first deploy can be slow)
- Clear browser cache
- Try incognito mode
- Check the exact URL (case sensitive)

## What URL Are You Trying?

The correct URL should be:
```
https://andrewnakas.github.io/GFS_Wave_Forecast/
```

NOT:
- https://andrewnakas.github.io/GFS_Wave_Forecast/index.html (might work but not needed)
- https://github.io/... (wrong domain)
- http:// (should be https)

## Quick Commands

Check Actions status:
```bash
# If gh CLI works:
gh run list --workflow=deploy.yml

# Or visit:
https://github.com/andrewnakas/GFS_Wave_Forecast/actions
```

Test locally right now:
```bash
cd /home/user/GFS_Wave_Forecast
python3 backend/simple_server.py
# Open: http://localhost:8000
```
