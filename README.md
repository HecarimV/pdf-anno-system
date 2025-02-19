# PDF Annotation System 📄

<div align="center">

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Django](https://img.shields.io/badge/django-4.2-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

基于 Django + PostgreSQL 的专业 PDF 标注系统，支持结构化标注、版本控制和进度追踪。

[English](./README_EN.md) | 简体中文

</div>

---

## ✨ 功能亮点

- 🔍 **智能预览** - PDF 文件在线预览，支持缩放和翻页
- 📝 **结构化标注** - 支持 JSON 格式的结构化标注
- ✅ **字段验证** - 字段级别的验证和进度追踪
- 🔄 **版本控制** - 完整的标注历史和版本回滚
- 🔐 **JWT 认证** - 安全的身份验证和授权
- 🐳 **容器化部署** - 支持 Docker 和 Kubernetes 部署

## 🛠️ 技术栈

- **Backend**
  - Python 3.11
  - Django 4.2
  - Django REST Framework
  - PostgreSQL
  - PyMuPDF
- **DevOps**
  - Docker
  - Kubernetes
  - Aliyun Container Registry

## 🚀 快速开始

### 🐳 Docker 部署

### 📁 文件操作

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/files/` | 上传文件 |
| GET | `/api/files/` | 获取文件列表 |
| GET | `/api/files/{id}/` | 获取文件详情 |
| DELETE | `/api/files/{id}/` | 删除文件 |
| GET | `/api/files/{id}/progress/` | 获取进度 |
| GET | `/api/files/{id}/history/` | 获取历史 |

### ✏️ 标注操作

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/annotations/?file_id={id}` | 获取标注 |
| PUT | `/api/annotations/{id}/verify/` | 验证字段 |
| PUT | `/api/annotations/{id}/edit_field/` | 编辑字段 |
| PUT | `/api/annotations/{id}/update_content/` | 更新内容 |
| POST | `/api/annotations/{id}/rollback/` | 回滚版本 |


## ⚙️ 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|---------|
| POSTGRES_DB | 数据库名称 | postgres |
| POSTGRES_USER | 数据库用户名 | postgres |
| POSTGRES_PASSWORD | 数据库密码 | - |
| POSTGRES_HOST | 数据库主机 | localhost |
| POSTGRES_PORT | 数据库端口 | 5432 |

## 📋 待办事项

- [ ] 添加批量导入功能
- [ ] 支持更多文件格式
- [ ] 添加用户权限管理
- [ ] 优化标注界面
- [ ] 添加数据导出功能

---

<div align="center">

如果这个项目对你有帮助，请给它一个 ⭐️

</div>

EOF

