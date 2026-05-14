package com.chaosplatform.orderapi.controller;

import java.net.URI;
import java.util.List;
import java.util.Map;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.chaosplatform.orderapi.model.PlaceOrderRequest;
import com.chaosplatform.orderapi.service.OrderRepository;
import com.chaosplatform.orderapi.service.OrderService.OrderNotFoundException;
import com.chaosplatform.orderapi.service.OrderService.OrderRetryNotAllowedException;
import com.chaosplatform.orderapi.service.OrderService;
import com.chaosplatform.orderapi.service.OrderService.QueuePublishException;

@RestController
public class OrderController {
    private final OrderService orderService;
    private final OrderRepository orderRepository;

    public OrderController(OrderService orderService, OrderRepository orderRepository) {
        this.orderService = orderService;
        this.orderRepository = orderRepository;
    }

    @GetMapping("/")
    public ResponseEntity<Void> root() {
        return ResponseEntity.status(HttpStatus.FOUND).location(URI.create("/dashboard.html")).build();
    }

    @GetMapping("/healthz")
    public Map<String, String> healthz() {
        return Map.of("status", "ok", "service", "order-api");
    }

    @GetMapping("/readyz")
    public ResponseEntity<Map<String, String>> readyz() {
        if (!orderRepository.ping()) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("status", "not-ready"));
        }
        return ResponseEntity.ok(Map.of("status", "ready"));
    }

    @PostMapping("/orders")
    public ResponseEntity<Map<String, Object>> placeOrder(@Valid @RequestBody PlaceOrderRequest request) {
        return ResponseEntity.accepted().body(orderService.placeOrder(request));
    }

    @GetMapping("/orders/{orderId}")
    public ResponseEntity<Map<String, Object>> getOrder(@PathVariable String orderId) {
        Map<String, Object> order = orderRepository.find(orderId);
        if (order == null || !"delivery_order".equals(order.get("job_type"))) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(order);
    }

    @PostMapping("/orders/{orderId}/retry")
    public ResponseEntity<Map<String, Object>> retryOrder(@PathVariable String orderId) {
        return ResponseEntity.accepted().body(orderService.retryFailedOrder(orderId));
    }

    @GetMapping("/orders")
    public List<Map<String, Object>> listOrders(@RequestParam(defaultValue = "50") int limit) {
        return orderRepository.listRecent(Math.max(1, Math.min(limit, 100)));
    }

    @GetMapping("/metrics")
    public Map<String, Integer> metrics() {
        return orderRepository.metrics();
    }

    @org.springframework.web.bind.annotation.ExceptionHandler(QueuePublishException.class)
    public ResponseEntity<Map<String, String>> queueUnavailable() {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("detail", "queue unavailable"));
    }

    @org.springframework.web.bind.annotation.ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<Map<String, String>> orderNotFound(OrderNotFoundException exc) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("detail", exc.getMessage()));
    }

    @org.springframework.web.bind.annotation.ExceptionHandler(OrderRetryNotAllowedException.class)
    public ResponseEntity<Map<String, String>> retryNotAllowed(OrderRetryNotAllowedException exc) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("detail", exc.getMessage()));
    }
}
