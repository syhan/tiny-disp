# 从Git历史记录中删除敏感数据
# Remove Sensitive Data from Git History

## ⚠️ 重要警告 / Important Warning

**此操作将重写整个Git历史记录！** / **This will rewrite entire Git history!**

- 在执行前请确保有完整备份 / Make sure you have a complete backup before proceeding
- 所有协作者需要重新克隆仓库 / All collaborators will need to re-clone the repository
- 此操作不可逆 / This operation is irreversible

## 🎯 目的 / Purpose

从Git历史记录中永久删除以下敏感信息：
Permanently remove the following sensitive information from Git history:

- TrueNAS IP地址: `10.0.0.129` → `YOUR_TRUENAS_IP`
- 用户名: `syhan` → `YOUR_USERNAME`
- 密码: `wssong` → `YOUR_PASSWORD`

## 📋 使用步骤 / Usage Steps

### 1. 备份当前仓库 / Backup Current Repository

```bash
# 创建备份 / Create backup
cd ..
cp -r tiny-disp tiny-disp-backup
cd tiny-disp
```

### 2. 确保工作目录干净 / Ensure Clean Working Directory

```bash
# 检查状态 / Check status
git status

# 如果有未提交的更改，先提交或stash
# If there are uncommitted changes, commit or stash them
git add .
git commit -m "Prepare for history rewrite"
# 或 / or
git stash
```

### 3. 执行清理脚本 / Run Cleanup Script

```bash
# 添加执行权限 / Add execute permission
chmod +x remove_sensitive.sh

# 运行脚本 / Run the script
./remove_sensitive.sh
```

脚本将会询问确认 / The script will ask for confirmation:
```
⚠️  WARNING: This will rewrite git history!
⚠️  Make sure you have a backup before proceeding.

Continue? (yes/no):
```

输入 `yes` 继续 / Type `yes` to continue.

### 4. 验证更改 / Verify Changes

```bash
# 检查历史记录 / Check history
git log --all --full-history --grep="10.0.0.129"
git log --all --full-history --grep="syhan"
git log --all --full-history --grep="wssong"

# 应该没有结果 / Should return no results

# 检查当前文件 / Check current files
grep -r "10.0.0.129" plugins/ legacy/
grep -r "syhan" plugins/ legacy/
grep -r "wssong" plugins/ legacy/

# 应该只显示占位符 / Should only show placeholders
```

### 5. 推送到远程仓库 / Push to Remote Repository

```bash
# 强制推送所有分支 / Force push all branches
git push origin --force --all

# 强制推送所有标签 / Force push all tags
git push origin --force --tags
```

### 6. 通知协作者 / Notify Collaborators

所有协作者需要：
All collaborators need to:

```bash
# 删除旧的本地仓库 / Delete old local repository
cd ..
rm -rf tiny-disp

# 重新克隆 / Re-clone
git clone <repository-url>
cd tiny-disp
```

## 🔄 恢复备份（如果需要）/ Restore Backup (if needed)

如果出现问题，可以从备份恢复：
If something goes wrong, restore from backup:

```bash
# 方法1: 使用备份分支 / Method 1: Use backup branch
git checkout backup-before-filter
git branch -D master  # 或其他分支 / or other branch
git checkout -b master

# 方法2: 使用完整备份 / Method 2: Use full backup
cd ..
rm -rf tiny-disp
mv tiny-disp-backup tiny-disp
cd tiny-disp
```

## 📝 脚本工作原理 / How the Script Works

脚本使用 `git filter-branch` 遍历整个Git历史：
The script uses `git filter-branch` to traverse entire Git history:

1. 创建备份分支 `backup-before-filter`
   Creates backup branch `backup-before-filter`

2. 对每个历史提交执行文本替换
   Performs text replacement on each historical commit

3. 在以下文件中替换敏感信息：
   Replaces sensitive information in the following files:
   - `plugins/plugin_zfs.py`
   - `plugins/plugin_zfs_pages.py`
   - `legacy/zfs.py`
   - `legacy/zfs_pages.py`

4. 重写所有引用这些文件的提交
   Rewrites all commits that reference these files

## ⚡ 替代方案 / Alternative Approaches

### 使用 BFG Repo-Cleaner (更快)

```bash
# 安装 / Install
brew install bfg  # macOS
# 或 / or
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# 创建替换文件 / Create replacement file
echo "10.0.0.129==>YOUR_TRUENAS_IP" > replacements.txt
echo "syhan==>YOUR_USERNAME" >> replacements.txt
echo "wssong==>YOUR_PASSWORD" >> replacements.txt

# 执行清理 / Run cleanup
bfg --replace-text replacements.txt

# 清理 / Cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 使用 git-filter-repo (推荐，但需要安装)

```bash
# 安装 / Install
pip3 install git-filter-repo

# 创建替换文件 / Create replacement file
cat > replacements.txt << 'EOF'
10.0.0.129==>YOUR_TRUENAS_IP
syhan==>YOUR_USERNAME
wssong==>YOUR_PASSWORD
EOF

# 执行清理 / Run cleanup
git filter-repo --replace-text replacements.txt

# 重新添加远程仓库 / Re-add remote
git remote add origin <repository-url>
git push origin --force --all
```

## 🛡️ 预防措施 / Prevention Measures

为了避免将来再次泄露敏感信息：
To prevent future leaks of sensitive information:

1. **使用配置文件** / **Use configuration files**
   ```ini
   # .tiny-disp.conf
   [zfs]
   host = 10.0.0.129
   user = syhan
   password = wssong
   ```

2. **添加到 .gitignore**
   ```
   .tiny-disp.conf
   *.conf
   !*.conf.sample
   ```

3. **使用环境变量** / **Use environment variables**
   ```python
   import os
   host = os.getenv('TRUENAS_HOST', 'YOUR_TRUENAS_IP')
   user = os.getenv('TRUENAS_USER', 'YOUR_USERNAME')
   password = os.getenv('TRUENAS_PASSWORD', 'YOUR_PASSWORD')
   ```

4. **使用 pre-commit hooks** / **Use pre-commit hooks**
   ```bash
   # .git/hooks/pre-commit
   if git grep -q "10.0.0.129\|syhan\|wssong"; then
       echo "Error: Sensitive data detected!"
       exit 1
   fi
   ```

## 📚 参考资源 / References

- [Git Filter-Branch Documentation](https://git-scm.com/docs/git-filter-branch)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [GitHub: Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

## ❓ 常见问题 / FAQ

### Q: 执行后仓库大小没有变化？
### Q: Repository size didn't change after execution?

A: 需要执行垃圾回收：
A: Need to run garbage collection:
```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Q: 远程推送被拒绝？
### Q: Remote push rejected?

A: 使用 `--force` 强制推送：
A: Use `--force` to force push:
```bash
git push origin --force --all
```

### Q: 如何验证敏感数据已完全删除？
### Q: How to verify sensitive data is completely removed?

A: 搜索整个历史：
A: Search entire history:
```bash
git log --all --full-history -S"10.0.0.129"
git grep "10.0.0.129" $(git rev-list --all)
