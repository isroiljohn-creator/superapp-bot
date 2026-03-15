#!/bin/bash
# Create symlink if it doesn't exist
if [ ! -e /Users/a1234/Documents/yashabot ]; then
    ln -s /Users/a1234/Documents/nuvi-academy-bot /Users/a1234/Documents/yashabot
fi

cd /Users/a1234/Documents/nuvi-academy-bot

# Remove helper scripts
rm -f push.sh deploy.sh

# Stage and commit
git add -A
git status
git diff --cached --stat

# Commit
git commit -m "feat: AI hodimlar coming soon + nixpacks simplified

- AI hodimlar button now shows 'ishlab chiqish jarayonida' message
- Removed npm/nodejs from nixpacks.toml (frontend pre-built)
- This should fix Railway deploy failures" 2>&1

# Push
git push origin main 2>&1

echo ""
echo "=== DEPLOY SCRIPT COMPLETE ==="
