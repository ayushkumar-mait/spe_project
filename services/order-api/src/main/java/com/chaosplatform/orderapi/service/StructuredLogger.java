package com.chaosplatform.orderapi.service;

import java.util.LinkedHashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class StructuredLogger {
    private static final Logger LOGGER = LoggerFactory.getLogger("order-api");

    private final ObjectMapper objectMapper;

    public StructuredLogger(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public void info(String message, Map<String, Object> fields) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("service", "order-api");
        payload.put("message", message);
        payload.putAll(fields);
        try {
            LOGGER.info(objectMapper.writeValueAsString(payload));
        } catch (Exception exc) {
            LOGGER.info("{} {}", message, fields);
        }
    }
}
