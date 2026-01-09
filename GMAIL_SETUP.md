# Gmail SMTP Setup Guide

This guide explains how to set up Gmail to send emails from the tennis league.

## Why This Is Needed

Gmail requires a special "App Password" to let applications send email on your behalf. This is more secure than using your regular password.

## Requirements

- A Gmail account (must be `@gmail.com`, not Google Workspace)
- 2-Step Verification enabled on the account

---

## Step-by-Step Instructions

### Step 1: Enable 2-Step Verification

If you already have 2-Step Verification enabled, skip to Step 2.

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification**
4. Click **Get Started**
5. Follow the prompts to set up a verification method (text message or authenticator app)
6. Complete the setup

### Step 2: Create an App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification**
4. Scroll to the bottom and click **App passwords**
   - If you don't see this option, 2-Step Verification may not be fully enabled
5. You may need to sign in again
6. In the "Select app" dropdown, choose **Mail**
7. In the "Select device" dropdown, choose **Other (Custom name)**
8. Type a name like `Tennis League`
9. Click **Generate**

### Step 3: Copy Your App Password

Google will show you a 16-character password like:

```
abcd efgh ijkl mnop
```

**Important:**
- Copy this password immediately - you won't be able to see it again
- Remove the spaces when you use it: `abcdefghijklmnop`
- Store it somewhere safe (password manager, secure note)

### Step 4: Add to Vercel

1. Go to your project on [vercel.com](https://vercel.com)
2. Click **Settings** > **Environment Variables**
3. Add a new variable:
   - Name: `SMTP_PASSWORD`
   - Value: Your 16-character app password (no spaces)
4. Click **Save**
5. Redeploy your project for changes to take effect

---

## Verification

To verify emails are working:

1. Visit `https://your-site.vercel.app/api/email`
2. You should see: `{"status": "ready"}`
3. If you see an error about SMTP_PASSWORD, check your environment variable

---

## Troubleshooting

### "App passwords" option not visible

- Make sure 2-Step Verification is fully enabled
- Sign out and back in to Google
- Try using an incognito/private browser window

### Authentication failed error

- Make sure you removed spaces from the password
- Verify the password was copied correctly (no extra characters)
- Generate a new app password and try again

### "Less secure apps" warning

- Ignore this - app passwords are the secure method
- Do NOT enable "Less secure app access" (it's being deprecated)

### Daily sending limits

Gmail allows ~100 emails per day for free accounts. If your league has:
- Under 25 players: No problem
- 25-100 players: Watch limits during high-email periods (1st of month)
- Over 100 players: Consider a dedicated email service (SendGrid, Mailgun)

---

## Rotating the Password

If you need to change the app password (e.g., someone left the team):

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Click the trash icon next to the old password
3. Create a new app password (follow Step 2 above)
4. Update the `SMTP_PASSWORD` in Vercel
5. Redeploy the project

---

## Security Notes

- App passwords can only be used for sending email, not for logging into Gmail
- Each app password should only be used for one application
- If you suspect the password is compromised, revoke it immediately
- The password is stored securely in Vercel's environment variables (encrypted at rest)
