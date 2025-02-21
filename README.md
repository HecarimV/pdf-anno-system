# PDF Annotation System 📄

<div align="center">

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Django](https://img.shields.io/badge/django-4.2-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Professional PDF Annotation System Built with Django & PostgreSQL

</div>

---

## ✨ Key Features

- 🔍 **Smart Preview** - Online PDF viewing with zoom and page navigation
- 📝 **Structured Annotations** - JSON-formatted annotations with field-level validation
- ✅ **Progress Tracking** - Real-time validation and completion monitoring
- 🔄 **Version Control** - Full audit history and version rollback
- 🔐 **JWT Authentication** - Secure token-based access control
- 🐳 **Cloud Ready** - Docker & Kubernetes deployment support

## 🛠️ Tech Stack

- **Backend**
  - Python 3.11
  - Django 4.2
  - Django REST Framework
  - PostgreSQL
  - PyMuPDF (Fitz)
- **Operations**
  - Docker
  - Kubernetes
  - Aliyun Container Registry

## 🚀 Getting Started

### 🐳 Docker Deployment

### 📄 File Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/files/` | Upload new file |
| GET | `/api/files/` | List all files |
| GET | `/api/files/{id}/` | Get file metadata |
| DELETE | `/api/files/{id}/` | Delete file |
| GET | `/api/files/{id}/progress/` | Check annotation progress |
| GET | `/api/files/{id}/history/` | View version history |

### ✍️ Annotation Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/annotations/?file_id={id}` | Retrieve annotations |
| PUT | `/api/annotations/{id}/verify/` | Validate field entry |
| PUT | `/api/annotations/{id}/edit_field/` | Modify field value |
| PUT | `/api/annotations/{id}/update_content/` | Update annotation content |
| POST | `/api/annotations/{id}/rollback/` | Restore previous version |

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_DB | Database name | postgres |
| POSTGRES_USER | Database user | postgres |
| POSTGRES_PASSWORD | Database password | - |
| POSTGRES_HOST | Database host | localhost |
| POSTGRES_PORT | Database port | 5432 |

## 📌 Roadmap

- [ ] Batch file import functionality
- [ ] Multi-format support (DOCX, PNG)
- [ ] RBAC implementation
- [ ] Annotation UI enhancements
- [ ] Data export capabilities (CSV/Excel)

---

<div align="center">

If this project helps you, please give it a ⭐️

</div>
