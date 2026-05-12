from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from kubernetes import client, config

from healing_controller.policy import HealingConfig, SystemSnapshot, decide_actions
from platform_common.logging import configure_json_logging
from platform_common.repository import RedisJobRepository
from platform_common.settings import load_settings


def main() -> None:
    settings = load_settings("healing-controller")
    logger = configure_json_logging("healing-controller", settings.log_level)
    repo = RedisJobRepository(settings.redis_url)
    namespace = os.getenv("TARGET_NAMESPACE", "job-platform")
    deployment = os.getenv("WORKER_DEPLOYMENT", "job-worker")
    interval = int(os.getenv("HEALING_INTERVAL_SECONDS", "15"))
    dry_run = os.getenv("HEALING_DRY_RUN", "false").lower() == "true"
    healing_config = HealingConfig(
        queued_threshold=int(os.getenv("HEALING_QUEUED_THRESHOLD", "10")),
        failed_threshold=int(os.getenv("HEALING_FAILED_THRESHOLD", "5")),
        min_replicas=int(os.getenv("HEALING_MIN_REPLICAS", "1")),
        max_replicas=int(os.getenv("HEALING_MAX_REPLICAS", "8")),
        scale_step=int(os.getenv("HEALING_SCALE_STEP", "1")),
    )

    apps_api = None if dry_run else _load_apps_api(logger)
    logger.info("healing_controller_started", extra={"event": "startup", "dry_run": dry_run})

    while True:
        metrics = repo.metrics()
        current_replicas = healing_config.min_replicas
        if apps_api is not None:
            current_replicas = _current_replicas(apps_api, namespace, deployment, healing_config.min_replicas)

        snapshot = SystemSnapshot(
            queued=metrics.queued,
            running=metrics.running,
            failed=metrics.failed,
            current_replicas=current_replicas,
        )
        actions = decide_actions(snapshot, healing_config)
        for action in actions:
            logger.warning(
                "healing_action_selected",
                extra={"event": "healing_action_selected", "action": action.action, "reason": action.reason},
            )
            if not dry_run and apps_api is not None:
                _apply_action(apps_api, namespace, deployment, action, logger)
        time.sleep(interval)


def _load_apps_api(logger: Any) -> client.AppsV1Api:
    try:
        config.load_incluster_config()
        logger.info("kubernetes_config_loaded", extra={"event": "kubernetes_config_loaded", "mode": "incluster"})
    except config.ConfigException:
        config.load_kube_config()
        logger.info("kubernetes_config_loaded", extra={"event": "kubernetes_config_loaded", "mode": "local"})
    return client.AppsV1Api()


def _current_replicas(
    apps_api: client.AppsV1Api,
    namespace: str,
    deployment: str,
    default: int,
) -> int:
    obj = apps_api.read_namespaced_deployment_scale(name=deployment, namespace=namespace)
    return int(obj.status.replicas or default)


def _apply_action(
    apps_api: client.AppsV1Api,
    namespace: str,
    deployment: str,
    action: Any,
    logger: Any,
) -> None:
    if action.action == "scale" and action.target_replicas is not None:
        body = {"spec": {"replicas": action.target_replicas}}
        apps_api.patch_namespaced_deployment_scale(name=deployment, namespace=namespace, body=body)
        logger.info(
            "deployment_scaled",
            extra={"event": "deployment_scaled", "deployment": deployment, "replicas": action.target_replicas},
        )
        return

    if action.action == "restart":
        restarted_at = datetime.now(timezone.utc).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "self-healing/restarted-at": restarted_at,
                        }
                    }
                }
            }
        }
        apps_api.patch_namespaced_deployment(name=deployment, namespace=namespace, body=body)
        logger.info(
            "deployment_restart_triggered",
            extra={"event": "deployment_restart_triggered", "deployment": deployment, "restarted_at": restarted_at},
        )


if __name__ == "__main__":
    main()

