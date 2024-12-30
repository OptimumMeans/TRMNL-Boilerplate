# TRMNL Plugin Setup Guide

This guide explains how to properly set up a new TRMNL plugin project using the TRMNL-Boilerplate repository.

## Initial Setup Steps

1. Create your new repository on GitHub
   - Go to GitHub and create a new repository
   - Name it according to your plugin (e.g., "TRMNL-FBI-Most-Wanted")
   - Don't initialize it with any files yet

2. Clone the boilerplate repository
   ```bash
   git clone https://github.com/OptimumMeans/TRMNL-Boilerplate.git YOUR-PLUGIN-NAME
   cd YOUR-PLUGIN-NAME
   ```

3. Remove the boilerplate remote connection
   ```bash
   git remote remove origin
   ```

4. Add your new repository as the origin
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-PLUGIN-NAME.git
   ```

5. Push to your new repository
   ```bash
   git add .
   git commit -m "Initial commit from boilerplate"
   git push -u origin main  # or master, depending on your default branch name
   ```

## Verification

To verify your setup is correct:

1. Check your remote URL:
   ```bash
   git remote -v
   ```
   This should show your new repository URL, not the boilerplate URL.

2. Visit your GitHub repository page
   - You should see all the boilerplate files in your repository
   - The commit history should start fresh with your initial commit

## Common Issues

- If `git push` tries to push to the boilerplate repository, you likely skipped step 3
- If you get a "repository not found" error, double check your new repository URL
- If you get a permission error, ensure you have the correct access rights to your new repository

## Next Steps

After setup, you can:
- Modify the plugin code for your specific needs
- Update the README.md to describe your plugin
- Configure your environment variables
- Begin development and testing

## Reference

Original boilerplate repository: https://github.com/OptimumMeans/TRMNL-Boilerplate.git