package com.chaosplatform.orderapi;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import org.junit.jupiter.api.Test;
import org.springframework.kafka.core.KafkaOperations;

import com.chaosplatform.orderapi.service.OrderJobFactory;
import com.chaosplatform.orderapi.service.OrderRepository;
import com.chaosplatform.orderapi.service.OrderService;
import com.chaosplatform.orderapi.service.StructuredLogger;
import com.fasterxml.jackson.databind.ObjectMapper;

class OrderServiceRetryTest {
    @Test
    void retriesFailedOrderAndLinksRecoveryJob() {
        KafkaOperations<String, String> kafkaTemplate = successfulKafkaOperations();
        StubOrderRepository repository = new StubOrderRepository();
        StructuredLogger logger = new StructuredLogger(new ObjectMapper());
        ObjectMapper objectMapper = new ObjectMapper();
        OrderJobFactory factory = new OrderJobFactory();
        OrderService service = new OrderService(
                "jobs",
                kafkaTemplate,
                objectMapper,
                repository,
                factory,
                logger);

        Map<String, Object> failedOrder = new LinkedHashMap<>();
        failedOrder.put("job_id", "failed-order-1");
        failedOrder.put("job_type", "delivery_order");
        failedOrder.put("status", "failed");
        failedOrder.put("payload", new LinkedHashMap<>(Map.of(
                "order_id", "failed-order-1",
                "customer_name", "Ayush",
                "restaurant_name", "Campus Canteen",
                "pickup_address", "Block A",
                "delivery_address", "Hostel Gate",
                "items", java.util.List.of("Paneer Roll"),
                "priority", 5,
                "estimated_distance_km", 2.5,
                "simulate_seconds", 2,
                "force_fail", true
        )));

        repository.store(failedOrder);
        Map<String, Object> response = service.retryFailedOrder("failed-order-1");

        assertThat(response).containsEntry("status", "queued");
        assertThat(response).containsEntry("retried_from", "failed-order-1");
        assertThat(response.get("order_id")).isNotEqualTo("failed-order-1");
        assertThat(repository.savedJobs).hasSize(1);
        Map<String, Object> savedJob = repository.savedJobs.get(0);
        assertThat(savedJob).containsEntry("job_type", "delivery_order");
        assertThat(savedJob).containsEntry("status", "queued");
        assertThat(savedJob).containsEntry("retry_of", "failed-order-1");
        assertThat(((Map<?, ?>) savedJob.get("payload")).get("force_fail")).isEqualTo(false);
        assertThat(repository.find("failed-order-1")).containsEntry("recovery_status", "resubmitted");
        assertThat(repository.find("failed-order-1").get("recovery_job_id")).isEqualTo(savedJob.get("job_id"));
    }

    @Test
    void rejectsRetryForNonFailedOrder() {
        KafkaOperations<String, String> kafkaTemplate = successfulKafkaOperations();
        StubOrderRepository repository = new StubOrderRepository();
        StructuredLogger logger = new StructuredLogger(new ObjectMapper());
        OrderService service = new OrderService(
                "jobs",
                kafkaTemplate,
                new ObjectMapper(),
                repository,
                new OrderJobFactory(),
                logger);

        repository.store(Map.of(
                "job_id", "order-1",
                "job_type", "delivery_order",
                "status", "completed",
                "payload", Map.of("order_id", "order-1")
        ));

        assertThatThrownBy(() -> service.retryFailedOrder("order-1"))
                .isInstanceOf(OrderService.OrderRetryNotAllowedException.class)
                .hasMessageContaining("only failed orders can be retried");
    }

    private static KafkaOperations<String, String> successfulKafkaOperations() {
        @SuppressWarnings("unchecked")
        KafkaOperations<String, String> kafkaOperations = (KafkaOperations<String, String>) Proxy.newProxyInstance(
                KafkaOperations.class.getClassLoader(),
                new Class<?>[] {KafkaOperations.class},
                (proxy, method, args) -> {
                    if ("send".equals(method.getName())) {
                        return CompletableFuture.completedFuture(null);
                    }
                    return defaultValue(method.getReturnType());
                });
        return kafkaOperations;
    }

    private static Object defaultValue(Class<?> returnType) {
        if (!returnType.isPrimitive() || returnType == Void.TYPE) {
            return null;
        }
        if (returnType == Boolean.TYPE) {
            return false;
        }
        if (returnType == Character.TYPE) {
            return '\0';
        }
        if (returnType == Byte.TYPE) {
            return (byte) 0;
        }
        if (returnType == Short.TYPE) {
            return (short) 0;
        }
        if (returnType == Integer.TYPE) {
            return 0;
        }
        if (returnType == Long.TYPE) {
            return 0L;
        }
        if (returnType == Float.TYPE) {
            return 0F;
        }
        if (returnType == Double.TYPE) {
            return 0D;
        }
        return null;
    }

    private static final class StubOrderRepository extends OrderRepository {
        private final Map<String, Map<String, Object>> jobs = new LinkedHashMap<>();
        private final List<Map<String, Object>> savedJobs = new ArrayList<>();

        private StubOrderRepository() {
            super(null, new ObjectMapper());
        }

        private void store(Map<String, Object> job) {
            jobs.put(String.valueOf(job.get("job_id")), new LinkedHashMap<>(job));
        }

        @Override
        public void save(Map<String, Object> job) {
            Map<String, Object> copy = new LinkedHashMap<>(job);
            savedJobs.add(copy);
            jobs.put(String.valueOf(job.get("job_id")), copy);
        }

        @Override
        public Map<String, Object> find(String orderId) {
            Map<String, Object> job = jobs.get(orderId);
            return job == null ? null : new LinkedHashMap<>(job);
        }

        @Override
        public void markFailed(String orderId, String error) {
            Map<String, Object> job = jobs.get(orderId);
            if (job == null) {
                return;
            }
            job.put("status", "failed");
            job.put("error", error);
        }

        @Override
        public void linkRecoveryJob(String failedOrderId, String recoveryJobId) {
            Map<String, Object> job = jobs.get(failedOrderId);
            if (job == null) {
                return;
            }
            job.put("recovery_job_id", recoveryJobId);
            job.put("recovery_status", "resubmitted");
        }
    }
}
