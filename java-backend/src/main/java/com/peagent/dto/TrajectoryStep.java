package com.peagent.dto;

import lombok.Data;

/**
 * 单个执行步骤（对应 Python Agent 返回的 trajectory 元素）。
 */
@Data
public class TrajectoryStep {

    private String action;
    private String message;
    private Boolean success;
}
