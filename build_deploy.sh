COMMMIT_MSG=$1

# Local production build command: bundle exec jekyll build JEKYLL_ENV=production 

# Build website for production
echo "Building site into deployment folder"
bundle exec jekyll build JEKYLL_ENV=production

# Go to _site folder and push to github
echo "Pushing to GitHub"
cd _site
git add .
git commit -m "$COMMIT_MSG"
git push origin master

echo "Site Deployed"