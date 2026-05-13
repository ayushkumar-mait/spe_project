package com.chaosplatform.orderapi.model;

import java.util.ArrayList;
import java.util.List;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

public class PlaceOrderRequest {
    @NotBlank
    private String customerName;

    @NotBlank
    private String restaurantName;

    @NotBlank
    private String pickupAddress;

    @NotBlank
    private String deliveryAddress;

    @NotEmpty
    private List<String> items = new ArrayList<>();

    @Min(1)
    @Max(10)
    private int priority = 5;

    @DecimalMin("0.1")
    @DecimalMax("100.0")
    private double estimatedDistanceKm = 3.0;

    @Min(0)
    @Max(30)
    private int simulateSeconds = 2;

    private boolean forceFail;

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    public String getRestaurantName() {
        return restaurantName;
    }

    public void setRestaurantName(String restaurantName) {
        this.restaurantName = restaurantName;
    }

    public String getPickupAddress() {
        return pickupAddress;
    }

    public void setPickupAddress(String pickupAddress) {
        this.pickupAddress = pickupAddress;
    }

    public String getDeliveryAddress() {
        return deliveryAddress;
    }

    public void setDeliveryAddress(String deliveryAddress) {
        this.deliveryAddress = deliveryAddress;
    }

    public List<String> getItems() {
        return items;
    }

    public void setItems(List<String> items) {
        this.items = items;
    }

    public int getPriority() {
        return priority;
    }

    public void setPriority(int priority) {
        this.priority = priority;
    }

    public double getEstimatedDistanceKm() {
        return estimatedDistanceKm;
    }

    public void setEstimatedDistanceKm(double estimatedDistanceKm) {
        this.estimatedDistanceKm = estimatedDistanceKm;
    }

    public int getSimulateSeconds() {
        return simulateSeconds;
    }

    public void setSimulateSeconds(int simulateSeconds) {
        this.simulateSeconds = simulateSeconds;
    }

    public boolean isForceFail() {
        return forceFail;
    }

    public void setForceFail(boolean forceFail) {
        this.forceFail = forceFail;
    }
}
