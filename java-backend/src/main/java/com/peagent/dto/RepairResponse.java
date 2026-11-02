package com.peagent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

/**
 * Python Agent /chat 的返回体。
 * 注意：Python 返回 snake_case（final_answer），Java 用 camelCase，
 * 需 @JsonProperty 显式映射。
 */
@Data
public class RepairResponse {

    private Boolean finished;

    @JsonProperty("final_answer")
    private String finalAnswer;

    private List<TrajectoryStep> trajectory;
}
