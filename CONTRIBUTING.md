# Contributing & Git Workflow

This document describes the git workflow used in this project.  
It's written for a solo developer learning git — every step is explained.

---

## 🌿 Branch Strategy

We use a simple **feature branch** workflow:

```
main          ← stable, always works
└── dev       ← integration branch (merge features here first)
    └── feat/gesture-detection   ← one branch per feature
    └── feat/arm-controller
    └── fix/thumb-detection-bug
```

**Rule:** never commit directly to `main`. Always go through a branch.

---

## 🚀 Starting a New Feature

```bash
# Make sure you're up to date
git checkout dev
git pull

# Create a new branch for your feature
git checkout -b feat/my-feature-name

# ... do your work ...

git add .
git commit -m "feat: describe what you did"

# Push your branch to GitHub
git push -u origin feat/my-feature-name
```

---

## ✅ Commit Message Format

Use this format so your history is readable:

```
<type>: <short description>

[optional body explaining why, not what]
```

| Type | When to use |
|------|-------------|
| `feat` | Adding a new feature |
| `fix` | Fixing a bug |
| `refactor` | Restructuring code (no behaviour change) |
| `docs` | README, comments, docstrings |
| `test` | Adding or fixing tests |
| `chore` | Build, config, dependencies |

**Examples:**
```
feat: add fist detection to right hand tracker
fix: thumb detection broken when hand is rotated
docs: update README with new topic names
refactor: split gesture logic into separate module
```

---

## 🔀 Merging Back to Dev

When your feature is done:

```bash
git checkout dev
git merge feat/my-feature-name

# If it works, delete the feature branch
git branch -d feat/my-feature-name
git push origin --delete feat/my-feature-name
```

---

## 🏷️ Releasing to Main

When `dev` is stable and tested:

```bash
git checkout main
git merge dev
git tag -a v0.1.0 -m "First working gesture detection"
git push && git push --tags
```

---

## 🧹 Useful Git Commands

```bash
git status                   # what changed?
git log --oneline --graph    # visual history
git diff                     # see uncommitted changes
git stash                    # temporarily save work in progress
git stash pop                # restore stashed work
```

---

## 🚫 What NOT to commit

See `.gitignore` — these are already excluded:
- `build/`, `install/`, `log/` (ROS 2 build artifacts)
- `__pycache__/`, `*.pyc`
- `.env` files (secrets)
- IDE files (`.vscode/`, `.idea/`)
