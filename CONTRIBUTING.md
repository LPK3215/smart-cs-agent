# Contributing to Smart CS Agent

感谢你对本项目的关注。欢迎提交 Issue、Pull Request 或反馈建议。

## 开发环境搭建

### 后端
```bash
cd smart-cs-server
python -m venv venv
venv/Scripts/pip install -r requirements.txt    # Windows
# venv/bin/pip install -r requirements.txt      # Linux/Mac
cp .env.example .env
# 编辑 .env 填入 API Key
venv/Scripts/python run.py
```

### 前端
```bash
cd smart-cs-web
npm install
npm run dev
```

## 代码规范

- **后端**: 遵循 PEP 8，使用 4 空格缩进。类型注解使用 Python 3.10+ 语法。
- **前端**: 使用 ESLint + TypeScript strict 模式，Vue 3 Composition API（`<script setup>`）。
- **提交信息**: 使用中文或英文均可，建议格式：`模块: 简短描述`（如 `agent: 修复 tool_calls 类型兼容`）。

## 分支策略

- `main` — 稳定版本，只接受经过测试的 PR
- 功能开发请在 feature 分支上进行（如 `feat/real-data-source`）
- 修复请直接基于 `main` 创建分支

## 提交 PR 前检查

```bash
# 后端
cd smart-cs-server
venv/Scripts/python -m py_compile app/*.py

# 前端
cd smart-cs-web
npx vue-tsc --noEmit
npm run build
```

## 项目结构约定

- 后端新模块放在 `smart-cs-server/app/` 下
- 前端新页面放在 `smart-cs-web/src/views/`，组件放在 `smart-cs-web/src/components/`
- 新增 Python 依赖需同步更新 `requirements.txt`
- 新增前端依赖需同步更新 `package.json`
- 新增配置项需同步更新 `.env.example`

## 联系方式

如有问题，请在 GitHub Issues 中提出，或通过邮件联系作者。
