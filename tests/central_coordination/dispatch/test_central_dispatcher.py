import pytest
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

@pytest.fixture
def dispatcher_setup():
    """Sets up a MessageBus and a CentralDispatcher with a standard rule set."""
    bus = MessageBus()
    rules = {
        "res1_flood_threshold": 9.0, "res1_drought_threshold": 3.0,
        "res1_normal_setpoint": 5.0, "res1_system_flood_setpoint": 4.0, "res1_system_drought_setpoint": 6.0,

        "res2_flood_threshold": 19.0, "res2_drought_threshold": 12.0,
        "res2_normal_setpoint": 15.0, "res2_system_flood_setpoint": 13.0, "res2_system_drought_setpoint": 17.0,
    }

    dispatcher = CentralDispatcher(
        agent_id="test_dispatcher",
        message_bus=bus,
        state_subscriptions={"res1": "state/res1", "res2": "state/res2"},
        command_topics={"res1_control": "command/res1", "res2_control": "command/res2"},
        rules=rules
    )

    # Listener to capture commands
    commands = {"res1": None, "res2": None}
    bus.subscribe("command/res1", lambda msg: commands.update({"res1": msg['new_setpoint']}))
    bus.subscribe("command/res2", lambda msg: commands.update({"res2": msg['new_setpoint']}))

    return bus, dispatcher, rules, commands

def test_dispatcher_normal_state(dispatcher_setup):
    """Tests that dispatcher sends 'normal' setpoints when levels are normal."""
    bus, dispatcher, rules, commands = dispatcher_setup

    # Publish normal state messages
    bus.publish("state/res1", {'water_level': 5.0})
    bus.publish("state/res2", {'water_level': 15.0})

    dispatcher.run(current_time=0)

    # No commands should be sent as the state is 'normal' from the start
    assert commands["res1"] is None
    assert commands["res2"] is None

def test_dispatcher_flood_state(dispatcher_setup):
    """Tests that dispatcher sends 'system_flood' setpoints when one reservoir is high."""
    bus, dispatcher, rules, commands = dispatcher_setup

    # res1 is in flood state
    bus.publish("state/res1", {'water_level': 9.5})
    bus.publish("state/res2", {'water_level': 15.0})

    dispatcher.run(current_time=0)

    # Check that flood setpoints were sent for BOTH reservoirs
    assert commands["res1"] == rules["res1_system_flood_setpoint"]
    assert commands["res2"] == rules["res2_system_flood_setpoint"]

def test_dispatcher_drought_state(dispatcher_setup):
    """Tests that dispatcher sends 'system_drought' setpoints when one reservoir is low."""
    bus, dispatcher, rules, commands = dispatcher_setup

    # res2 is in drought state
    bus.publish("state/res1", {'water_level': 5.0})
    bus.publish("state/res2", {'water_level': 11.0})

    dispatcher.run(current_time=0)

    # Check that drought setpoints were sent
    assert commands["res1"] == rules["res1_system_drought_setpoint"]
    assert commands["res2"] == rules["res2_system_drought_setpoint"]

def test_dispatcher_flood_overrides_drought(dispatcher_setup):
    """Tests that a flood alert in one reservoir takes precedence over a drought in another."""
    bus, dispatcher, rules, commands = dispatcher_setup

    # res1 is in flood, res2 is in drought
    bus.publish("state/res1", {'water_level': 9.5})
    bus.publish("state/res2", {'water_level': 11.0})

    dispatcher.run(current_time=0)

    # Flood profile should be active, overriding the drought
    assert dispatcher.active_setpoint_name == "system_flood"
    assert commands["res1"] == rules["res1_system_flood_setpoint"]
    assert commands["res2"] == rules["res2_system_flood_setpoint"]
