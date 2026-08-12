---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "GitHub Repository Fork Detachment Guide"
timestamp: "2026-08-08T14:00:00+08:00"
topics: ["github", "git", "fork", "best-practices", "governance"]
---

**[DEVOPS EXECUTION]**

# 🛡️ GitHub Repository Fork Detachment & Independence Guide

This guide outlines standard operating procedures and best practices for detaching a GitHub repository fork (e.g., `linuxmalaysia/aws-3tier-deployment-for-php-infra` from its parent `SongketMail/aws-3tier-deployment-for-ai-infra`).

When a fork's feature sets, configurations, and core scope deviate significantly from the parent repository (such as shifting from an AI-centric infrastructure to a specialized PHP CodeIgniter deployment), detaching them into fully independent repositories is recommended. This prevents accidental synchronization, unauthorized pull request modifications, and ensures that codebases are maintained with clear boundaries.

---

## ⚠️ Key Considerations Before Detachment

Before proceeding with detachment, evaluate and back up the following elements of your repository:

1. **Commit History:** Detachment preserves your full Git commit history (all branches and tags), but you must verify that your local copies are complete and up to date.
2. **Stars & Watchers:**
   - **Method 1 (GitHub Support)** preserves all stars and watchers.
   - **Method 2 (Manual Re-creation)** resets stars and watchers to zero.
3. **Issues & Pull Requests:**
   - **Method 1** retains existing issues and pull requests but severs active PR linkages pointing to the parent repository.
   - **Method 2** deletes all existing issues, pull requests, and releases on GitHub.
4. **GitHub Pages & CI/CD Actions:** After detachment, ensure that your custom GitHub Pages domains and secret environment variables (e.g., AWS credentials, deployment keys) are preserved or re-configured.

---

## 🛠️ Method 1: Contacting GitHub Support (Recommended)

This is the cleanest and most reliable way to detach a repository. It preserves all stars, watchers, watchers history, forks, issues, PRs, and wiki pages while cleanly breaking the fork relationship.

### 📋 Step-by-Step Instructions

1. **Navigate to the GitHub Support Portal:**
   Go to [GitHub Support](https://support.github.com/).
2. **Interact with the GitHub Virtual Assistant:**
   - Under the chat or virtual assistant prompt, type: `detach fork` or `make repository independent`.
   - The virtual assistant will guide you through an automated wizard.
3. **Select Your Repository:**
   - Select your user/organization account (`linuxmalaysia`) and the repository you want to detach (`aws-3tier-deployment-for-php-infra`).
4. **Confirm the Action:**
   - Confirm that you wish to break the connection with `SongketMail/aws-3tier-deployment-for-ai-infra`.
   - The Virtual Assistant can often perform this operation **instantly and automatically** for public and private repositories.
5. **Verify Detachment:**
   - Navigate back to your repository page on GitHub.
   - Verify that the subtitle `forked from SongketMail/aws-3tier-deployment-for-ai-infra` has disappeared from the top-left area beneath the repository name.

---

## 🛠️ Method 2: Manual Duplication (Immediate Self-Service)

If you need immediate independence and do not want to wait for support or run into assistant limitations, you can duplicate your repository manually. This involves backing up the codebase, deleting the fork, and uploading the repository as a standalone.

> 🔴 **DANGER:** Deleting the fork repository on GitHub will permanently delete its associated issues, PRs, stars, watchers, releases, and wiki pages. Ensure you have full backups before proceeding.

### 📋 Step-by-Step Instructions

#### Step 2.1: Clone a Bare Copy of the Repository
Create a clean bare clone of your fork, which contains all branches, tags, and commits:
```bash
git clone --bare https://github.com/linuxmalaysia/aws-3tier-deployment-for-php-infra.git
```

#### Step 2.2: Delete the Existing Fork on GitHub
1. Navigate to your repository: `https://github.com/linuxmalaysia/aws-3tier-deployment-for-php-infra`.
2. Click on the **Settings** tab at the top.
3. Scroll down to the very bottom to find the **Danger Zone**.
4. Click **Delete this repository**.
5. Follow the verification prompts (typing your repository name and/or entering a 2FA code) to confirm the deletion.

#### Step 2.3: Create a Brand New Standalone Repository
1. On GitHub, click the **`+`** icon in the top right and select **New repository**.
2. Set the repository name to exactly: `aws-3tier-deployment-for-php-infra`.
3. Set the visibility (Public/Private) to match your previous setup.
4. **Do NOT** initialize the repository with a README, `.gitignore`, or license (keep it completely empty).

#### Step 2.4: Mirror-Push Your Code to the New Repository
Push all backed-up branches, commits, and tags to your new standalone repository:
```bash
cd aws-3tier-deployment-for-php-infra.git
git push --mirror https://github.com/linuxmalaysia/aws-3tier-deployment-for-php-infra.git
```

#### Step 2.5: Clean Up Local Backups
Once the mirror-push succeeds and you verify that all branches are visible on GitHub, you can safely delete the temporary bare clone:
```bash
cd ..
rm -rf aws-3tier-deployment-for-php-infra.git
```

---

## 🔄 Post-Detachment Checklist

After completing either method, complete these additional tasks:

- [ ] **Configure Git Remotes:** Ensure your developers' local repositories point to the correct standalone URL.
- [ ] **Verify CI/CD Actions:** Confirm that GitHub Actions or other CI/CD integrations are triggered successfully on pushes.
- [ ] **Re-enable GitHub Pages:** If you are serving documentation via GitHub Pages, re-enable it in the repository **Settings** -> **Pages** tab.
- [ ] **Re-assign Org Permissions & Collaborators:** Re-invite external collaborators and re-configure team write permissions if you used Method 2.
