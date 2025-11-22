# Gmail App Password Setup for Ashley

## Quick Guide (5 minutes)

### Step 1: Go to Google Account Settings
1. Go to: https://myaccount.google.com
2. Click "Security" in the left menu

### Step 2: Enable 2-Step Verification
1. Scroll to "Signing in to Google"
2. Click "2-Step Verification"
3. If not enabled, click "Get Started" and follow steps
4. Use your phone number for verification

### Step 3: Create App Password
1. Still in "Security" section
2. Click "App passwords" (it's under "Signing in to Google")
3. Under "Select app" choose: **Mail**
4. Under "Select device" choose: **Other (Custom name)**
5. Type: **NET WORTH Tennis**
6. Click "Generate"

### Step 4: Copy the Password
1. Google will show a **16-character password** like: `abcd efgh ijkl mnop`
2. Copy this password immediately (you'll only see it once!)

### Step 5: Update Code
1. Open file: `/home/ubuntu/dev/networth/networth_complete.py`
2. Go to line 456
3. Replace `'YOUR_APP_PASSWORD'` with the copied password

### That's it! 🎉

The app password allows our system to send emails without giving away Ashley's main password. It's much more secure than using the regular password.