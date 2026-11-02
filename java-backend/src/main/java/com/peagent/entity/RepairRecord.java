package com.peagent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 对话记录实体，对应表 repair_record。
 */
@Data
@TableName("repair_record")
public class RepairRecord {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String goal;

    private String finalAnswer;

    /** success / failed */
    private String status;

    private LocalDateTime createTime;
}
