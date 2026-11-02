# 09 · Java 前后端运行指南（方案 A 初版已落地）

> 三端架构：**Vue3 前端 → Spring Boot(Java) 后端 → Python Agent**。
> 数据库用 H2 内存库（零安装），Java 用 WebClient 调 Python Agent。

```mermaid
flowchart LR
    F["浏览器 Vue3<br/>:5173"] -->|"/api/repair"| J["Spring Boot Java<br/>:8080"]
    J -->|WebClient "/chat"| P["Python Agent FastAPI<br/>:8000"]
    J --> DB[("H2 内存库")]
```

---

## 一、先决条件

| 工具 | 需要 | 你机器现状 |
|---|---|---|
| JDK 17+ | ✅ 必须 | ❌ 未装 |
| Maven（或 IDEA 自带） | ✅ 必须 | ❌ 未装 |
| Node 18+ / npm | ✅ 必须 | ✅ 已装 v22 |

> **JDK 17 安装**：去 [Adoptium Temurin](https://adoptium.net/) 或 [Oracle JDK](https://www.oracle.com/java/technologies/downloads/) 下载 JDK 17/21，一路下一步，安装完命令行能跑 `java -version` 即可。
> **Maven**：若用 IntelliJ IDEA（社区版免费）打开 java-backend，IDEA 自带 Maven，可跳过单独安装。

---

## 二、启动顺序（三个终端）

### 1️⃣ 先起 Python Agent（端口 8000）

```bash
cd E:/pycharm/project/PE_saver_agent
.venv/Scripts/python.exe -m uvicorn pe_agent.api.main:app --host 127.0.0.1 --port 8000
# 或（需 PYTHONPATH=src）
# PYTHONPATH=src .venv/Scripts/python.exe -m uvicorn pe_agent.api.main:app --port 8000
```

验证：浏览器开 `http://127.0.0.1:8000/docs` 能看到 Swagger 即可。

### 2️⃣ 再起 Java 后端（端口 8080）

方式 A（IDEA）：用 IDEA 打开 `java-backend` 目录 → 等 Maven 下载完依赖 → 运行 `PeAgentApplication`。

方式 B（命令行）：
```bash
cd E:/pycharm/project/PE_saver_agent/java-backend
mvn spring-boot:run
```

验证：浏览器开 `http://localhost:8080/api/health` 返回 `{"code":0,...}`。

### 3️⃣ 最后起前端（端口 5173）

```bash
cd E:/pycharm/project/PE_saver_agent/frontend
npm install        # 首次需要，下载依赖
npm run dev
```

验证：浏览器开 `http://localhost:5173`，输入故障描述点「开始救援」。

---

## 三、接口速查

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/health` | GET | 健康检查 |
| `/api/repair` | POST | 传 `{"goal":"..."}`，转发 Python Agent 并落库 |
| `/api/records` | GET | 查询最近对话记录（`?limit=20`） |
| `/h2-console` | - | H2 控制台（JDBC URL 填 `jdbc:h2:mem:peagent`） |

---

## 四、关键设计点（面试可讲）

1. **跨语言微服务调用**：Java 用 WebClient 调 Python Agent 的 REST 接口，两服务解耦——这是「Java 后端 + AI 能力服务」的标准姿势。
2. **MyBatis-Plus + H2**：ORM 用国内最主流的 MyBatis-Plus，DB 用 H2 零安装；切 MySQL 只改 `application.yml` 的 `datasource` + 加驱动依赖。
3. **统一返回结构**：`Result<T>`（code/msg/data），前端据此统一处理成功/失败。
4. **snake_case ↔ camelCase**：Python 返回 `final_answer`，Java 用 `@JsonProperty("final_answer")` 显式映射（跨语言协作的常见坑）。
5. **CORS + Vite 代理**：开发期前端经 Vite proxy 转发 `/api` 到 8080，后端也开了 CORS，双保险。

---

## 五、以后切 MySQL（可选，Phase 2）

1. `pom.xml` 加 `mysql-connector-j`，移除或保留 h2；
2. `application.yml` 改：
   ```yaml
   spring:
     datasource:
       url: jdbc:mysql://localhost:3306/peagent?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
       username: root
       password: 你的密码
       driver-class-name: com.mysql.cj.jdbc.Driver
   ```
3. 建表语句不变（H2 的 schema.sql 与 MySQL 兼容）。
