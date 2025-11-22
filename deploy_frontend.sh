#!/bin/bash
# Deploy NET WORTH to Vercel Production

echo "🚀 Deploying NET WORTH to Vercel..."
echo ""
echo "Option 1: Auto-deploy (if GitHub integration is set up)"
echo "  → Merge your PR and Vercel will auto-deploy"
echo "  → PR: https://github.com/Khamel83/networth/pull/new/claude/complete-site-links-019PGcB4YSVqTYBZWjyYoHVY"
echo ""
echo "Option 2: Manual deploy with Vercel CLI"
echo "  → Run: vercel --prod"
echo ""
echo "Checking if Vercel CLI is installed..."

if command -v vercel &> /dev/null; then
    echo "✅ Vercel CLI found"
    echo ""
    echo "Deploy to production? This will make the new pages live."
    echo "Run: vercel --prod"
else
    echo "❌ Vercel CLI not installed"
    echo "Install: npm i -g vercel"
    echo "Then run: vercel --prod"
fi
