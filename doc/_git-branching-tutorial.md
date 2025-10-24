# Git Branching Tutorial Guide

## **Best Online Git Branch Tutorials**

### **1. Learn Git Branching (Highly Recommended - Visual & Interactive)**
- **URL**: https://learngitbranching.js.org/
- **Description**: Interactive visual tutorial specifically for branching
- **Why it's great**: You can see exactly what each command does to the branch structure in real-time

### **2. Atlassian Git Branching Tutorial**
- **URL**: https://www.atlassian.com/git/tutorials/using-branches
- **Description**: Comprehensive tutorial with examples and workflows
- **Coverage**: Basic branching, merging strategies, and advanced workflows

### **3. Official Git Book - Branching Chapter**
- **URL**: https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell
- **Description**: Deep dive into Git branching concepts from the official documentation
- **Best for**: Understanding the technical details and concepts

### **4. GitHub Flow Guide**
- **URL**: https://guides.github.com/introduction/flow/
- **Description**: Simple branching workflow for GitHub collaboration
- **Best for**: Team workflows and GitHub integration

### **5. Official Git Documentation**
- **Git Official Tutorial**: https://git-scm.com/docs/gittutorial
- **Git Branching Guide**: https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell
- **Pro Git Book** (Free): https://git-scm.com/book

## **Essential Branching Commands**

### **Creating and Switching Branches**
```bash
# Create a new branch
git branch feature-name

# Switch to existing branch
git checkout feature-name

# Create and switch to new branch (shortcut)
git checkout -b feature-name

# Modern Git: switch to branch
git switch feature-name

# Modern Git: create and switch to new branch
git switch -c feature-name
```

### **Viewing Branches**
```bash
# List local branches
git branch

# List all branches (local and remote)
git branch -a

# List remote branches only
git branch -r

# Show current branch
git branch --show-current
```

### **Working with Branches**
```bash
# See which branch you're on
git status

# Rename current branch
git branch -m new-name

# Rename specific branch
git branch -m old-name new-name

# Delete local branch (safe - prevents deletion if not merged)
git branch -d feature-name

# Force delete local branch
git branch -D feature-name
```

### **Merging Branches**
```bash
# Switch to target branch (usually main/master)
git checkout main

# Merge feature branch into current branch
git merge feature-name

# Merge with no fast-forward (creates merge commit)
git merge --no-ff feature-name

# Abort merge if conflicts arise
git merge --abort
```

### **Remote Branch Operations**
```bash
# Push branch to remote
git push origin feature-name

# Push and set upstream tracking
git push -u origin feature-name

# Delete remote branch
git push origin --delete feature-name

# Fetch all remote branches
git fetch --all

# Create local branch from remote branch
git checkout -b feature-name origin/feature-name
```

## **Common Branching Workflows**

### **Feature Branch Workflow**
```bash
# 1. Start from main branch
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/new-feature

# 3. Work on feature, commit changes
git add .
git commit -m "Add new feature functionality"

# 4. Push feature branch
git push -u origin feature/new-feature

# 5. Create pull request (on GitHub/GitLab)
# 6. After approval, merge via web interface or:

# 7. Switch to main and merge locally
git checkout main
git pull origin main
git merge feature/new-feature

# 8. Delete feature branch
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

### **Hotfix Workflow**
```bash
# 1. Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# 2. Fix the bug and commit
git add .
git commit -m "Fix critical bug"

# 3. Push and merge quickly
git push -u origin hotfix/critical-bug

# 4. Merge to main
git checkout main
git merge hotfix/critical-bug
git push origin main

# 5. Clean up
git branch -d hotfix/critical-bug
git push origin --delete hotfix/critical-bug
```

## **Branch Naming Conventions**

### **Common Patterns**
```
feature/feature-name        # New features
bugfix/issue-description    # Bug fixes
hotfix/critical-fix         # Critical production fixes
release/version-number      # Release preparation
chore/maintenance-task      # Maintenance tasks
docs/documentation-update   # Documentation changes
```

### **Examples**
```
feature/user-authentication
feature/shopping-cart
bugfix/login-error
hotfix/security-patch
release/v2.1.0
chore/update-dependencies
docs/api-documentation
```

## **Handling Merge Conflicts**

### **When Conflicts Occur**
```bash
# 1. Attempt merge
git merge feature-branch

# 2. If conflicts, Git will show:
# Auto-merging file.txt
# CONFLICT (content): Merge conflict in file.txt
# Automatic merge failed; fix conflicts and then commit the result.

# 3. View conflicted files
git status

# 4. Edit files to resolve conflicts (remove conflict markers)
# 5. Stage resolved files
git add resolved-file.txt

# 6. Complete the merge
git commit

# Or abort if needed
git merge --abort
```

## **Best Practices**

### **Branch Management**
- Keep branches focused on single features or fixes
- Use descriptive branch names
- Regularly sync with main branch
- Delete merged branches promptly
- Don't work directly on main/master

### **Commit Practices**
- Make small, focused commits
- Write clear commit messages
- Commit frequently while working
- Test before pushing

### **Merge Strategies**
- **Merge commits**: Preserves branch history
- **Squash and merge**: Creates single commit
- **Rebase and merge**: Linear history

## **Troubleshooting Common Issues**

### **Switch Branch with Uncommitted Changes**
```bash
# Option 1: Stash changes
git stash
git checkout other-branch
git checkout original-branch
git stash pop

# Option 2: Commit changes first
git add .
git commit -m "WIP: work in progress"
git checkout other-branch

# Option 3: Force checkout (loses changes)
git checkout -f other-branch
```

### **Accidentally Committed to Wrong Branch**
```bash
# Move last commit to new branch
git branch new-branch
git reset --hard HEAD~1
git checkout new-branch
```

### **Reset Branch to Remote State**
```bash
# Discard all local changes and match remote
git fetch origin
git reset --hard origin/branch-name
```

---

## **Quick Reference Card**

| Action | Command |
|--------|---------|
| Create branch | `git checkout -b branch-name` |
| Switch branch | `git checkout branch-name` |
| List branches | `git branch -a` |
| Merge branch | `git merge branch-name` |
| Delete branch | `git branch -d branch-name` |
| Push branch | `git push -u origin branch-name` |
| Pull changes | `git pull origin main` |

---

*For more advanced Git operations, see the `git-common-commands.md` file in this same directory.*