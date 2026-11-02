package com.peagent;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * PE-Agent Java 后端入口。
 * 职责：接收前端请求 → 调 Python Agent → 落库 → 返回结果。
 */
@SpringBootApplication
@MapperScan("com.peagent.mapper")
public class PeAgentApplication {

    public static void main(String[] args) {
        SpringApplication.run(PeAgentApplication.class, args);
    }
}
