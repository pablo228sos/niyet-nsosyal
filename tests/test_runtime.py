import pytest

from niyet.runtime import NiyetRuntime
from niyet.types import IntentType


runtime = NiyetRuntime()


def test_normal_post_does_not_enter_routing():
    result = runtime.route(
        "Bugün prototipin ilk benchmark koşusunu tamamladık. Sonuçları yarın paylaşacağız."
    )

    assert result.response_needed is False
    assert result.intent is None
    assert result.responder_id is None


def test_robotics_help_routes_to_control_profile():
    result = runtime.route(
        "Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?"
    )

    assert result.response_needed is True
    assert result.intent == "ask"
    assert result.responder_id == "r_control"
    assert result.development_utility is not None


def test_fastapi_collaboration_routes_to_backend_profile():
    result = runtime.route(
        "Hafta sonu prototipi için FastAPI bilen bir ekip arkadaşı arıyorum. Birlikte çalışmak isteyen var mı?"
    )

    assert result.response_needed is True
    assert result.intent == "collaborate"
    assert result.responder_id == "r_backend"


def test_manual_intent_can_override_false_negative_gate():
    text = "Bugün küçük bir backend denemesi yaptım."
    result = runtime.route(text, intent_override=IntentType.FEEDBACK)

    assert result.response_needed is True
    assert result.intent == "feedback"


def test_accept_action_reduces_session_capacity():
    state = runtime.default_responder_state()
    before = int(state["r_backend"]["remaining_slots"])

    updated = runtime.update_responder_state(state, "r_backend", action="accept")

    assert int(updated["r_backend"]["remaining_slots"]) == max(0, before - 1)


def test_pause_removes_responder_from_next_route():
    state = runtime.default_responder_state()
    state = runtime.update_responder_state(state, "r_control", action="pause")

    result = runtime.route(
        "Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?",
        responder_state=state,
    )

    assert result.responder_id != "r_control"


def test_batch_routing_respects_shared_capacity():
    state = runtime.default_responder_state()
    for responder_id in state:
        state[responder_id]["remaining_slots"] = 1
        state[responder_id]["active"] = True

    decisions = runtime.route_many(
        [
            {
                "id": "robot-1",
                "text": "Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?",
                "intent_override": IntentType.ASK,
            },
            {
                "id": "robot-2",
                "text": "Mini drone projesi için kontrol algoritmaları bilen bir ekip arkadaşı arıyoruz.",
                "intent_override": IntentType.COLLABORATE,
            },
        ],
        responder_state=state,
    )

    assigned = [item.responder_id for item in decisions if item.responder_id]
    assert len(assigned) == len(set(assigned))


def test_batch_routing_rejects_duplicate_request_ids():
    with pytest.raises(ValueError, match="duplicate_request_id"):
        runtime.route_many(
            [
                {"id": "same", "text": "Python API konusunda yardım?", "intent_override": IntentType.ASK},
                {"id": "same", "text": "FastAPI konusunda yardım?", "intent_override": IntentType.ASK},
            ]
        )
