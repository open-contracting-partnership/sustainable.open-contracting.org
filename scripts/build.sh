#!/bin/sh
# Build a site and its search index into _site/<lang>/: scripts/build.sh en|es|fr
# Set JEKYLL_ENV=production to include Google Analytics.
set -eu
lang="$1"
bundle exec jekyll build --config "_config.yml,_config.$lang.yml"
npx -y pagefind@1.5.2 --site "_site/$lang"
