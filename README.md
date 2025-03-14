# VJudge后端

使用FastAPI、MySQL、Redis和Tortoise ORM构建的在线评判平台后端。

## 特点

- 使用JWT进行用户身份验证
- 请求速率限制
- 用户配置文件管理
- 筛选和分页
- 通知系统
- 标签和来源管理
- Redis缓存
- 使用Tortoise ORM的MySQL数据库

## 先决条件

- Python 3.8+（此项目使用3.12）
- MySQL
- Redis
- 虚拟环境（推荐）

## 部署

1. 克隆存储库
2. 创建并激活虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. 安装依赖项：

```bash
pip install -r requirements.txt
```

4. 配置环境变量：

- 复制 .env.example 文件并重命名为 .env
- 在 .env 文件中更新配置值

5. 初始化数据库：

```bash
aerich init -t app.main.TORTOISE_ORM
aerich init-db
```

6. 迁移数据库:

```bash
aerich migrate
aerich upgrade
```

## 运行应用程序

开发：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

生产：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

或

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
```

## API文档

应用程序运行后，您可以访问：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 项目结构

```text
.
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── notices.py
│   │   │   ├── questions.py
│   │   │   ├── sources.py
│   │   │   ├── tags.py
│   │   │   └── users.py
│   │   ├── api.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   ├── log_config.py
│   │   └── security.py
│   ├── models.py
│   ├── schemas.py
│   └── main.py
├── .env
├── requirements.txt
└── README.md
```

## 安全性

- 使用bcrypt进行密码哈希
- JWT身份验证
- CORS中间件
- 敏感数据的环境变量

## 贡献

1. 分叉存储库
2. 创建特征分支
3. 提交你的更改
4. 推到分支
5. 创建新的Pull Request

## 许可证

该项目根据MIT许可证获得许可。
