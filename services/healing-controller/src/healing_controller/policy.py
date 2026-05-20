from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealingConfig:
    queued_threshold: int = 10
    failed_threshold: int = 5
    min_replicas: int = 1
    max_replicas: int = 8
    scale_step: int = 1


@dataclass(frozen=True)
class SystemSnapshot:
    queued: int
    running: int
    failed: int
    current_replicas: int

    @property
    def backlog(self) -> int:
        return self.queued + self.running


@dataclass(frozen=True)
class HealingAction:
    action: str
    reason: str
    target_replicas: int | None = None


def decide_actions(
    snapshot: SystemSnapshot,
    config: HealingConfig,
    last_restart_failed_count: int | None = None,
) -> list[HealingAction]:
    actions: list[HealingAction] = []

    if snapshot.backlog > config.queued_threshold:
        extra_batches = max(1, snapshot.backlog // max(config.queued_threshold, 1))
        target = min(
            config.max_replicas,
            max(snapshot.current_replicas + config.scale_step, extra_batches + config.min_replicas),
        )
        if target > snapshot.current_replicas:
            actions.append(
                HealingAction(
                    action="scale",
                    target_replicas=target,
                    reason=f"backlog {snapshot.backlog} exceeded threshold {config.queued_threshold}",
                )
            )

    should_restart = snapshot.failed >= config.failed_threshold
    if last_restart_failed_count is not None:
        should_restart = should_restart and snapshot.failed > last_restart_failed_count

    if should_restart:
        actions.append(
            HealingAction(
                action="restart",
                reason=f"failed jobs {snapshot.failed} reached threshold {config.failed_threshold}",
            )
        )

    if snapshot.backlog == 0 and snapshot.current_replicas > config.min_replicas:
        actions.append(
            HealingAction(
                action="scale",
                target_replicas=config.min_replicas,
                reason="backlog cleared; return to minimum replicas",
            )
        )

    return actions
