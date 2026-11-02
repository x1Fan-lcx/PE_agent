package com.peagent.common;

import lombok.Data;

/**
 * 统一返回结构：{code, msg, data}。
 * code=0 表示成功，非 0 表示失败（对齐前端统一处理）。
 */
@Data
public class Result<T> {

    private int code;
    private String msg;
    private T data;

    public static <T> Result<T> success(T data) {
        Result<T> r = new Result<>();
        r.code = 0;
        r.msg = "ok";
        r.data = data;
        return r;
    }

    public static <T> Result<T> error(String msg) {
        Result<T> r = new Result<>();
        r.code = 1;
        r.msg = msg;
        return r;
    }
}
