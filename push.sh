#!/bin/bash
cd /Users/a1234/Documents/nuvi-academy-bot
git add -A
git status
git commit -m "feat: AI hodimlar - coming soon message + nixpacks simplified" 2>&1 || echo "Nothing to commit"
git push origin main 2>&1
echo "=== DONE ==="
