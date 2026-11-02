-- 对话记录表（H2 内存库，启动时自动建）
CREATE TABLE IF NOT EXISTS repair_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    goal VARCHAR(500) NOT NULL,
    final_answer VARCHAR(2000),
    status VARCHAR(20),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
