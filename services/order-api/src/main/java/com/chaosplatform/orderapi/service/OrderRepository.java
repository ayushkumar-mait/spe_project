package com.chaosplatform.orderapi.service;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import org.springframework.data.redis.connection.RedisConnection;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

@Repository
public class OrderRepository {
    private static final TypeReference<LinkedHashMap<String, Object>> JOB_MAP = new TypeReference<>() {};

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

    public OrderRepository(StringRedisTemplate redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    public void save(Map<String, Object> job) {
        String jobId = Objects.toString(job.get("job_id"));
        redisTemplate.opsForValue().set(jobKey(jobId), toJson(job));
        redisTemplate.opsForList().leftPush(listKey(), jobId);
        redisTemplate.opsForList().trim(listKey(), 0, 499);
    }

    public Map<String, Object> find(String orderId) {
        String raw = redisTemplate.opsForValue().get(jobKey(orderId));
        if (raw == null) {
            return null;
        }
        return fromJson(raw);
    }

    public List<Map<String, Object>> listRecent(int limit) {
        List<String> ids = redisTemplate.opsForList().range(listKey(), 0, Math.max(limit - 1, 0));
        if (ids == null) {
            return List.of();
        }
        return ids.stream()
                .map(this::find)
                .filter(Objects::nonNull)
                .filter(job -> "delivery_order".equals(job.get("job_type")))
                .collect(Collectors.toList());
    }

    public Map<String, Integer> metrics() {
        Map<String, Integer> counts = new LinkedHashMap<>();
        counts.put("queued", 0);
        counts.put("running", 0);
        counts.put("completed", 0);
        counts.put("failed", 0);
        counts.put("cancelled", 0);

        for (Map<String, Object> job : listRecent(500)) {
            String status = Objects.toString(job.get("status"), "queued");
            if (counts.containsKey(status)) {
                counts.put(status, counts.get(status) + 1);
            }
        }

        int total = counts.values().stream().mapToInt(Integer::intValue).sum();
        counts.put("total", total);
        counts.put("backlog", counts.get("queued") + counts.get("running"));
        return counts;
    }

    public boolean ping() {
        RedisConnection connection = null;
        try {
            connection = Objects.requireNonNull(redisTemplate.getConnectionFactory()).getConnection();
            return "PONG".equalsIgnoreCase(connection.ping());
        } catch (Exception exc) {
            return false;
        } finally {
            if (connection != null) {
                connection.close();
            }
        }
    }

    public void markFailed(String orderId, String error) {
        Map<String, Object> job = find(orderId);
        if (job == null) {
            return;
        }
        job.put("status", "failed");
        job.put("error", error);
        job.put("updated_at", OffsetDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
        redisTemplate.opsForValue().set(jobKey(orderId), toJson(job));
    }

    private String toJson(Map<String, Object> job) {
        try {
            return objectMapper.writeValueAsString(job);
        } catch (Exception exc) {
            throw new IllegalStateException("Failed to serialize order job", exc);
        }
    }

    private Map<String, Object> fromJson(String raw) {
        try {
            return objectMapper.readValue(raw, JOB_MAP);
        } catch (Exception exc) {
            throw new IllegalStateException("Failed to deserialize order job", exc);
        }
    }

    private String jobKey(String jobId) {
        return "jobs:" + jobId;
    }

    private String listKey() {
        return "jobs:recent";
    }
}
