package com.chaosplatform.orderapi.service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaOperations;
import org.springframework.stereotype.Service;

import com.chaosplatform.orderapi.model.PlaceOrderRequest;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class OrderService {
    private final String topic;
    private final KafkaOperations<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final OrderRepository orderRepository;
    private final OrderJobFactory orderJobFactory;
    private final StructuredLogger structuredLogger;

    public OrderService(
            @Value("${platform.job-topic}") String topic,
            KafkaOperations<String, String> kafkaTemplate,
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
        return enqueueJob(job, null);
    }

    public Map<String, Object> retryFailedOrder(String failedOrderId) {
        Map<String, Object> existing = orderRepository.find(failedOrderId);
        if (existing == null || !"delivery_order".equals(existing.get("job_type"))) {
            throw new OrderNotFoundException("order not found");
        }

        String status = Objects.toString(existing.get("status"), "queued");
        if (!"failed".equals(status)) {
            throw new OrderRetryNotAllowedException("only failed orders can be retried");
        }

        Map<String, Object> retryJob = orderJobFactory.createRetryDeliveryJob(existing);
        return enqueueJob(retryJob, failedOrderId);
    }

    private Map<String, Object> enqueueJob(Map<String, Object> job, String retriedFromOrderId) {
        String orderId = Objects.toString(job.get("job_id"));
        String traceId = Objects.toString(job.get("trace_id"));

        orderRepository.save(job);
        try {
            kafkaTemplate.send(topic, orderId, objectMapper.writeValueAsString(job)).get(10, TimeUnit.SECONDS);
        } catch (Exception exc) {
            orderRepository.markFailed(orderId, "publish failed: " + exc.getMessage());
            throw new QueuePublishException("queue unavailable", exc);
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> payload = (Map<String, Object>) job.get("payload");

        if (retriedFromOrderId != null) {
            orderRepository.linkRecoveryJob(retriedFromOrderId, orderId);
            structuredLogger.info("order_retry_submitted", Map.of(
                    "event", "order_retry_submitted",
                    "order_id", orderId,
                    "retried_from", retriedFromOrderId,
                    "trace_id", traceId,
                    "restaurant_name", Objects.toString(payload.get("restaurant_name"), "unknown"),
                    "priority", payload.get("priority")));
        } else {
            structuredLogger.info("order_submitted", Map.of(
                    "event", "order_submitted",
                    "order_id", orderId,
                    "trace_id", traceId,
                    "restaurant_name", Objects.toString(payload.get("restaurant_name"), "unknown"),
                    "priority", payload.get("priority")));
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("order_id", orderId);
        response.put("job_id", orderId);
        response.put("status", "queued");
        response.put("trace_id", traceId);
        if (retriedFromOrderId != null) {
            response.put("retried_from", retriedFromOrderId);
        }
        return response;
    }

    public static class OrderNotFoundException extends RuntimeException {
        public OrderNotFoundException(String message) {
            super(message);
        }
    }

    public static class OrderRetryNotAllowedException extends RuntimeException {
        public OrderRetryNotAllowedException(String message) {
            super(message);
        }
    }

    public static class QueuePublishException extends RuntimeException {
        public QueuePublishException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
