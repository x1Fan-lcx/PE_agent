package com.peagent.controller;

import com.peagent.common.Result;
import com.peagent.dto.RepairRequest;
import com.peagent.dto.RepairResponse;
import com.peagent.entity.RepairRecord;
import com.peagent.service.RepairService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST 接口层。
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class RepairController {

    private final RepairService repairService;

    /** 健康检查 */
    @GetMapping("/health")
    public Result<Map<String, String>> health() {
        return Result.success(Map.of("status", "ok", "service", "pe-agent-java"));
    }

    /** 发起一次系统救援 */
    @PostMapping("/repair")
    public Result<RepairResponse> repair(@Valid @RequestBody RepairRequest req) {
        try {
            return Result.success(repairService.repair(req.getGoal()));
        } catch (Exception e) {
            return Result.error("调用失败：" + e.getMessage());
        }
    }

    /** 查询最近对话记录 */
    @GetMapping("/records")
    public Result<List<RepairRecord>> records(@RequestParam(defaultValue = "20") int limit) {
        return Result.success(repairService.listRecords(limit));
    }
}
