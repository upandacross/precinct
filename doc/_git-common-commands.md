# Git Common Commands Reference

## **Commands to List Files**

| Command | Purpose |
|---------|---------|
| `git status` | Shows modified, staged, and untracked files |
| `git ls-files` | Lists all files tracked by git |
| `git ls-tree HEAD --name-only` | Lists files in current commit (top level only) |
| `git ls-tree -r HEAD --name-only` | Lists all files in current commit (recursive) |
| `git diff --name-only` | Lists only the names of changed files |
| `git diff --name-status` | Lists changed files with their status (A/M/D) |

### **Most commonly used:**
- **`git ls-files`** - Shows all tracked files
- **`git status`** - Shows current working directory status

## **Basic Git Commands**

### **Repository Status & Information**
```bash
git status                    # Show working directory status
git log                       # Show commit history
git log --oneline            # Show compact commit history
git branch                   # List local branches
git branch -a                # List all branches (local and remote)
git remote -v                # Show remote repositories
```

### **Working with Files**
```bash
git add <file>               # Stage a specific file
git add .                    # Stage all changes
git add -A                   # Stage all changes (including deletions)
git commit -m "message"      # Commit staged changes
git commit -am "message"     # Stage and commit all changes
```

### **Branching & Merging**
```bash
git branch <name>            # Create new branch
git checkout <branch>        # Switch to branch
git checkout -b <name>       # Create and switch to new branch
git merge <branch>           # Merge branch into current branch
git branch -d <name>         # Delete local branch
```

### **Remote Operations**
```bash
git push                     # Push commits to remote
git push -u origin <branch>  # Push and set upstream
git pull                     # Fetch and merge from remote
git fetch                    # Fetch changes without merging
git clone <url>              # Clone remote repository
```

### **Viewing Changes**
```bash
git diff                     # Show unstaged changes
git diff --staged            # Show staged changes
git diff <commit1> <commit2> # Compare commits
git show <commit>            # Show commit details
```

### **Undoing Changes**
```bash
git restore <file>           # Discard changes in working directory
git restore --staged <file>  # Unstage file
git reset HEAD~1             # Undo last commit (keep changes)
git reset --hard HEAD~1      # Undo last commit (discard changes)
git revert <commit>          # Create new commit that undoes changes
```

### **Stashing**
```bash
git stash                    # Stash current changes
git stash pop                # Apply most recent stash
git stash list               # List all stashes
git stash apply <stash>      # Apply specific stash
git stash drop <stash>       # Delete specific stash
```

### **File History & Blame**
```bash
git log --follow <file>      # Show history of a file
git blame <file>             # Show who changed each line
git log -p <file>            # Show changes to file over time
```

### **Configuration**
```bash
git config --global user.name "Name"     # Set global username
git config --global user.email "email"   # Set global email
git config --list                        # Show all config settings
git config --global --list               # Show global config
```

## **Advanced Commands**

### **Interactive Operations**
```bash
git add -i                   # Interactive staging
git rebase -i HEAD~n         # Interactive rebase
git commit --amend           # Amend last commit
```

### **Search & Find**
```bash
git grep "pattern"           # Search for pattern in tracked files
git log --grep="pattern"     # Search commit messages
git log -S "string"          # Search for string in file contents
```

### **Working with Tags**
```bash
git tag                      # List tags
git tag <name>               # Create lightweight tag
git tag -a <name> -m "msg"   # Create annotated tag
git push --tags              # Push tags to remote
```

---

*This reference covers the most commonly used git commands for daily development work.*