# 餐饮 / 酒店智能排班管理系统（GitHub 自动生成 EXE）

本项目使用 GitHub Actions 在 Windows 云端编译 Windows `.exe`，你不需要在自己的电脑安装 Python 或 PyInstaller。

## 一、上传到 GitHub

1. 登录 https://github.com/
2. 点击右上角 `+` → `New repository`。
3. 仓库名称可填写 `hotel-roster`，选择 Public 或 Private 均可。
4. 点击 `Create repository`。
5. 在仓库页面点击 `Add file` → `Upload files`。
6. 将本项目文件夹内的所有内容上传，**包括隐藏的 `.github` 文件夹**。
   - `排班管理系统.py`
   - `.github/workflows/build-windows.yml`
   - `README.md`
7. 点击 `Commit changes` 保存。

## 二、生成 EXE

上传到 `main` 或 `master` 分支后会自动开始编译。

也可以手动启动：
1. 打开 GitHub 仓库。
2. 点击顶部 `Actions`。
3. 左侧选择 `Build Windows EXE`。
4. 点击 `Run workflow` → 再点击绿色 `Run workflow`。

## 三、下载 EXE

1. 在 `Actions` 中点击最新一次运行记录。
2. 等待所有步骤显示绿色勾号。
3. 在页面底部 `Artifacts` 区域，点击 `餐饮酒店智能排班管理系统-Windows` 下载。
4. 解压下载的 ZIP，即可得到：
   `餐饮酒店智能排班管理系统.exe`
5. 将 EXE 放在你有写入权限的文件夹中，双击运行。

## 注意事项

- 每次提交代码到 `main` / `master` 都会自动重新编译。
- GitHub Actions 生成的 Artifact 默认保留 30 天，请及时下载。
- 软件首次启动会在 EXE 同目录创建 `schedule_data.json`，用于保存员工和排班数据；请定期备份。
- 本项目当前是基础 MVP：支持员工管理、两班倒 / 三班倒、自动排班、手动调整和 CSV 导出。排班结果请管理人员核对后再发布。
- Windows 可能对未签名程序显示 SmartScreen 提示；请确认文件来自自己的 GitHub 仓库。
