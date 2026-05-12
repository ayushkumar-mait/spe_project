from healing_controller.policy import HealingConfig, SystemSnapshot, decide_actions


def test_scales_workers_when_backlog_is_high():
    actions = decide_actions(
        SystemSnapshot(queued=25, running=3, failed=0, current_replicas=2),
        HealingConfig(queued_threshold=10, min_replicas=1, max_replicas=5),
    )

    assert actions[0].action == "scale"
    assert actions[0].target_replicas == 3


def test_restarts_workers_when_failures_cross_threshold():
    actions = decide_actions(
        SystemSnapshot(queued=0, running=0, failed=6, current_replicas=1),
        HealingConfig(failed_threshold=5),
    )

    assert any(action.action == "restart" for action in actions)


def test_scales_down_after_backlog_clears():
    actions = decide_actions(
        SystemSnapshot(queued=0, running=0, failed=0, current_replicas=4),
        HealingConfig(min_replicas=1),
    )

    assert actions == [
        actions[0],
    ]
    assert actions[0].target_replicas == 1

