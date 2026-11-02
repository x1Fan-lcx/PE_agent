package com.peagent.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 前端 → 后端的请求体：故障描述。
 */
@Data
public class RepairRequest {

    @NotBlank(message = "故障描述不能为空")
    private String goal;
}
