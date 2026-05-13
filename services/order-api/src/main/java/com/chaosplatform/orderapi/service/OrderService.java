package com.chaosplatform.orderapi.service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import com.chaosplatform.orderapi.model.PlaceOrderRequest;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class OrderService {
    private final String topic;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final OrderRepository orderRepository;
    private final OrderJobFactory orderJobFactory;
    private final StructuredLogger structuredLogger;

    public OrderService(
            @Value("${platform.job-topic}") String topic,
            KafkaTemplate<String, String> kafkaTemplate,
            ObjectMapper objectMapper,
            OrderRepository orderRepository,
            OrderJobFactory orderJobFactory,
            StructuredLogger structuredLogger) {
        this.topic = topic;
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
        this.orderRepository = orderRepository;
        this.orderJobFactory = orderJobFactory;
        this.structuredLogger = structuredLogger;
    }

    public Map<String, Object> placeOrder(PlaceOrderRequest request) {
        Map<String, Object> job = orderJobFactory.createDeliveryJob(request);
        String orderId = Objects.toString(job.get("job_id"));
        String traceId = Objects.toString(job.get("trace_id"));

        orderRepository.save(job);
        try {
            kafkaTemplate.send(topic, orderId, objectMapper.writeValueAsString(job)).get(10, TimeUnit.SECONDS);
        } catch (Exception exc) {
            orderRepository.markFailed(orderId, "publish failed: " + exc.getMessage());
            throw new QueuePublishException("queue unavailable", exc);
        }

        structuredLogger.info("order_submitted", Map.of(
                "event", "order_submitted",
                "order_id", orderId,
                "trace_id", traceId,
                "restaurant_name", request.getRestaurantName(),
                "priority", request.getPriority()));

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("order_id", orderId);
        response.put("job_id", orderId);
        response.put("status", "queued");
        response.put("trace_id", traceId);
        return response;
    }

    public static class QueuePublishException extends RuntimeException {
        public QueuePublishException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
