# 🔑 Token负载均衡系统使用说明

## 📋 系统概述

这是一个完整的Token负载均衡系统，包含以下组件：

1. **Token管理器** (`token_manager.py`) - 端口8000
2. **Web API服务** (`wopan_web_api.py`) - 端口5000  
3. **Token客户端** (`token_client.py`) - 库文件
4. **服务启动器** (`start_services.py`) - 一键启动

## 🚀 快速开始

### 方法1: 一键启动（推荐）

```bash
python start_services.py
```

这将自动启动所有服务并进行测试。

### 方法2: 手动启动

1. **启动Token管理器**
```bash
python token_manager.py
```

2. **启动Web API服务**
```bash
python wopan_web_api.py
```

## 🌐 服务地址

- **Token管理器**: http://localhost:8000 (需要登录)
- **Web API服务**: http://localhost:5000

## 🔐 登录信息

**Token管理器Web界面需要登录：**
- **用户名**: `admin`
- **密码**: `3150261994`

**注意**: API端点 (`/api/*`) 无需认证，用于服务间调用

## 🔧 Token管理

### Web界面管理

访问 http://localhost:8000 可以看到Token管理界面，支持：

- 📊 查看Token统计信息
- ➕ 添加新Token
- 🗑️ 删除Token
- 📈 查看成功率和使用情况

### API管理

#### 获取Token
```bash
curl "http://localhost:8000/api/token/get?strategy=best"
```

#### 添加Token
```bash
curl -X POST "http://localhost:8000/api/token/add" \
  -H "Content-Type: application/json" \
  -d '{"token": "your-new-token", "name": "新Token"}'
```

#### 删除Token
```bash
curl -X DELETE "http://localhost:8000/api/token/remove" \
  -H "Content-Type: application/json" \
  -d '{"token": "token-to-remove"}'
```

#### 查看统计
```bash
curl "http://localhost:8000/api/token/stats"
```

## 📊 负载均衡策略

### 1. 轮询模式 (round_robin)
- 按顺序轮流使用Token
- 适合Token性能相近的情况

### 2. 最佳模式 (best)
- 根据成功率和使用时间选择最佳Token
- 自动避开失败率高的Token
- **推荐使用**

## 🔄 自动故障转移

系统具备智能故障转移功能：

1. **自动禁用**: 当Token错误率过高时自动禁用
2. **健康检查**: 定期检查Token状态
3. **负载均衡**: 自动分配请求到健康的Token

## 📈 监控和统计

### 实时统计信息

- 总Token数量
- 活跃Token数量
- 总请求数
- 整体成功率
- 每个Token的详细统计

### 使用报告

系统自动记录：
- 成功/失败次数
- 最后使用时间
- 错误信息
- 成功率计算

## 🛠️ 配置文件

### tokens.json
```json
{
  "tokens": [
    {
      "token": "your-token-here",
      "name": "主Token",
      "is_active": true
    }
  ]
}
```

## 🧪 测试API

### 测试文件夹列表
```bash
curl "http://localhost:5000/api/folders?realtime=true"
```

### 测试文件列表
```bash
curl "http://localhost:5000/api/files?folder=BD-another&realtime=true"
```

### 测试下载地址
```bash
curl "http://localhost:5000/api/download/?url=BD-another/01.mp4"
```

## 🔍 故障排除

### 1. Token管理器无法启动
- 检查端口8000是否被占用
- 确保tokens.json文件格式正确

### 2. Web API无法获取Token
- 确保Token管理器正在运行
- 检查网络连接到localhost:8000

### 3. Token被自动禁用
- 检查Token是否过期
- 查看错误日志确定问题原因
- 在Web界面查看详细统计

### 4. 实时API失败
- 检查Token是否有效
- 确认网络连接正常
- 系统会自动回退到缓存模式

## 📝 日志说明

### Token管理器日志
```
✅ 加载了 X 个token
✅ 添加新token: Token名称
⚠️ Token XXX 因错误率过高被暂时禁用
```

### Web API日志
```
✅ 获取到token: Token名称
✅ 实时API找到文件: 文件名
⚠️ 回退到缓存查找
```

## 🎯 最佳实践

1. **多Token配置**: 配置多个有效Token以提高可用性
2. **监控统计**: 定期查看Token使用统计
3. **及时更新**: Token过期前及时更新
4. **负载分散**: 使用"best"策略自动优化负载

## 🔒 安全建议

1. **Token保护**: 不要在日志中完整显示Token
2. **访问控制**: 在生产环境中限制管理接口访问
3. **定期轮换**: 定期更新Token以提高安全性

## 📞 技术支持

如遇问题，请检查：
1. 服务启动日志
2. Token统计信息
3. 网络连接状态
4. Token有效性
