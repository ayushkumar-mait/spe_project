package com.chaosplatform.orderapi.service;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

import org.springframework.stereotype.Component;

import com.chaosplatform.orderapi.model.PlaceOrderRequest;

@Component
public class OrderJobFactory {
    public Map<String, Object> createDeliveryJob(PlaceOrderRequest request) {
        String orderId = UUID.randomUUID().toString();
        String traceId = UUID.randomUUID().toString();
        String now = OffsetDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("order_id", orderId);
        payload.put("customer_name", request.getCustomerName());
        payload.put("restaurant_name", request.getRestaurantName());
        payload.put("pickup_address", request.getPickupAddress());
        payload.put("delivery_address", request.getDeliveryAddress());
        payload.put("items", request.getItems());
        payload.put("priority", request.getPriority());
        payload.put("estimated_distance_km", request.getEstimatedDistanceKm());
        payload.put("simulate_seconds", request.getSimulateSeconds());
        payload.put("force_fail", request.isForceFail());

        Map<String, Object> job = new LinkedHashMap<>();
        job.put("job_id", orderId);
        job.put("job_type", "delivery_order");
        job.put("payload", payload);
        job.put("status", "queued");
        job.put("created_at", now);
        job.put("updated_at", now);
        job.put("result", null);
        job.put("error", null);
        job.put("attempts", 0);
        job.put("trace_id", traceId);
        return job;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> createRetryDeliveryJob(Map<String, Object> existingJob) {
        String orderId = UUID.randomUUID().toString();
        String traceId = UUID.randomUUID().toString();
        String now = OffsetDateTime.now(ZoneOffset.UTC).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);

        Map<String, Object> existingPayload = (Map<String, Object>) existingJob.get("payload");
        Map<String, Object> payload = new LinkedHashMap<>(existingPayload == null ? Map.of() : existingPayload);
        payload.put("order_id", orderId);
        payload.put("force_fail", false);

        Map<String, Object> job = new LinkedHashMap<>();
        job.put("job_id", orderId);
        job.put("job_type", Objects.toString(existingJob.get("job_type"), "delivery_order"));
        job.put("payload", payload);
        job.put("status", "queued");
        job.put("created_at", now);
        job.put("updated_at", now);
        job.put("result", null);
        job.put("error", null);
        job.put("attempts", 0);
        job.put("trace_id", traceId);
        job.put("retry_of", existingJob.get("job_id"));
        return job;
    }
}
