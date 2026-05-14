package com.chaosplatform.orderapi;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import com.chaosplatform.orderapi.model.PlaceOrderRequest;
import com.chaosplatform.orderapi.service.OrderJobFactory;

class OrderJobFactoryTest {
    @Test
    void createsWorkerCompatibleDeliveryJob() {
        PlaceOrderRequest request = new PlaceOrderRequest();
        request.setCustomerName("Ayush");
        request.setRestaurantName("Campus Canteen");
        request.setPickupAddress("Block A");
        request.setDeliveryAddress("Hostel Gate");
        request.setItems(List.of("Paneer Roll", "Cold Coffee"));
        request.setEstimatedDistanceKm(2.5);
        request.setPriority(7);
        request.setSimulateSeconds(1);

        Map<String, Object> job = new OrderJobFactory().createDeliveryJob(request);

        assertThat(job).containsEntry("job_type", "delivery_order");
        assertThat(job).containsEntry("status", "queued");
        assertThat(job).containsKeys("job_id", "trace_id", "created_at", "updated_at");

        @SuppressWarnings("unchecked")
        Map<String, Object> payload = (Map<String, Object>) job.get("payload");
        assertThat(payload).containsEntry("customer_name", "Ayush");
        assertThat(payload).containsEntry("restaurant_name", "Campus Canteen");
        assertThat(payload).containsEntry("priority", 7);
    }

    @Test
    void createsRetryJobThatClearsForcedFailureAndLinksOriginalJob() {
        PlaceOrderRequest request = new PlaceOrderRequest();
        request.setCustomerName("Ayush");
        request.setRestaurantName("Campus Canteen");
        request.setPickupAddress("Block A");
        request.setDeliveryAddress("Hostel Gate");
        request.setItems(List.of("Paneer Roll"));
        request.setPriority(5);
        request.setEstimatedDistanceKm(2.5);
        request.setSimulateSeconds(2);
        request.setForceFail(true);

        OrderJobFactory factory = new OrderJobFactory();
        Map<String, Object> original = factory.createDeliveryJob(request);
        original.put("status", "failed");

        Map<String, Object> retry = factory.createRetryDeliveryJob(original);

        assertThat(retry).containsEntry("job_type", "delivery_order");
        assertThat(retry).containsEntry("status", "queued");
        assertThat(retry).containsEntry("retry_of", original.get("job_id"));
        assertThat(retry.get("job_id")).isNotEqualTo(original.get("job_id"));

        @SuppressWarnings("unchecked")
        Map<String, Object> payload = (Map<String, Object>) retry.get("payload");
        assertThat(payload).containsEntry("force_fail", false);
        assertThat(payload).containsEntry("customer_name", "Ayush");
        assertThat(payload.get("order_id")).isEqualTo(retry.get("job_id"));
    }
}
