package com.peagent.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.peagent.dto.RepairResponse;
import com.peagent.entity.RepairRecord;
import com.peagent.mapper.RepairRecordMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 业务编排：调用 Python Agent 的 /chat，并把结果落库。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RepairService {

    private final WebClient agentWebClient;
    private final RepairRecordMapper recordMapper;

    /**
     * 发起一次系统救援：转发故障描述给 Python Agent，返回其决策轨迹与结论。
     */
    public RepairResponse repair(String goal) {
        // 1. 调用 Python Agent
        RepairResponse resp = agentWebClient.post()
                .uri("/chat")
                .bodyValue(Map.of("goal", goal))
                .retrieve()
                .bodyToMono(RepairResponse.class)
                .block();

        if (resp == null) {
            throw new IllegalStateException("Python Agent 返回为空，请确认其已启动(端口 8000)");
        }

        // 2. 落库（失败不阻断主流程，仅记录日志）
        try {
            RepairRecord record = new RepairRecord();
            record.setGoal(goal);
            record.setFinalAnswer(resp.getFinalAnswer());
            record.setStatus(Boolean.TRUE.equals(resp.getFinished()) ? "success" : "failed");
            record.setCreateTime(LocalDateTime.now());
            recordMapper.insert(record);
        } catch (Exception e) {
            log.warn("对话记录落库失败（不影响主流程）: {}", e.getMessage());
        }

        return resp;
    }

    /**
     * 查询最近的对话记录。
     */
    public List<RepairRecord> listRecords(int limit) {
        int n = Math.max(1, Math.min(limit, 100));
        return recordMapper.selectList(
                new QueryWrapper<RepairRecord>().orderByDesc("id").last("LIMIT " + n)
        );
    }
}
