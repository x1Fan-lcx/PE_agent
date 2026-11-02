package com.peagent.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * WebClient 配置：用于调用 Python Agent 的 FastAPI 服务。
 */
@Configuration
public class WebClientConfig {

    @Value("${agent.python-url:http://127.0.0.1:8000}")
    private String pythonUrl;

    @Bean
    public WebClient agentWebClient(WebClient.Builder builder) {
        return builder
                .baseUrl(pythonUrl)
                .build();
    }
}
