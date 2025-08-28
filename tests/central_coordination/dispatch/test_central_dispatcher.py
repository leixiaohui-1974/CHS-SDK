import pytest
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.central_coordination.collaboration.message_bus import MessageBus

@pytest.fixture
def dispatcher_setup():
    """Sets up a dispatcher with a bus, profile-based rules, and command listeners."""
    bus = MessageBus()

    rules = {
        "profiles": {
            "flood": {
                "condition": lambda states: states.get('res1', {}).get('water_level', 0) > 9.0,
                "commands": {
                    "res1_control": {"new_setpoint": 4.0, "mode": "emergency"},
                    "res2_control": {"new_setpoint": 14.0}
                }
            },
            "drought": {
                "condition": lambda states: states.get('res2', {}).get('water_level', 0) < 12.0,
                "commands": {
                    "res1_control": {"new_setpoint": 6.0},
                    "res2_control": {"new_setpoint": 16.0, "mode": "conserve"}
                }
            },
            "normal": {
                "condition": lambda states: True,
                "commands": {
                    "res1_control": {"new_setpoint": 5.0},
                    "res2_control": {"new_setpoint": 15.0}
                }
            }
        }
    }

    commands = {'res1': None, 'res2': None}

    def res1_command_listener(msg):
        commands['res1'] = msg

    def res2_command_listener(msg):
        commands['res2'] = msg

    bus.subscribe("command/res1", res1_command_listener)
    bus.subscribe("command/res2", res2_command_listener)

    dispatcher = CentralDispatcher(
        agent_id="test_dispatcher",
        message_bus=bus,
        state_subscriptions={"res1": "state/res1", "res2": "state/res2"},
        command_topics={"res1_control": "command/res1", "res2_control": "command/res2"},
        rules=rules
    )

    return bus, dispatcher, rules, commands

def test_dispatcher_switches_to_normal_state(dispatcher_setup):
    """
    Tests that the dispatcher correctly switches back to the 'normal' profile
    and sends the appropriate commands.
    """
    bus, dispatcher, rules, commands = dispatcher_setup

    # 1. First, put the system in a flood state to move it away from the initial 'normal' state
    bus.publish("state/res1", {'water_level': 9.5})
    bus.publish("state/res2", {'water_level': 15.0})
    dispatcher.run(current_time=0)
    assert dispatcher.active_setpoint_name == "flood" # Verify it's in flood mode

    # 2. Now, publish a normal state and check that it switches back and sends commands
    bus.publish("state/res1", {'water_level': 5.0})
    bus.publish("state/res2", {'water_level': 15.0})
    dispatcher.run(current_time=1)

    assert dispatcher.active_setpoint_name == "normal"
    assert commands["res1"] == rules["profiles"]["normal"]["commands"]["res1_control"]
    assert commands["res2"] == rules["profiles"]["normal"]["commands"]["res2_control"]


def test_dispatcher_flood_state(dispatcher_setup):
    """Tests that the dispatcher activates the 'flood' profile when conditions are met."""
    bus, dispatcher, rules, commands = dispatcher_setup

    bus.publish("state/res1", {'water_level': 9.5}) # Flood condition
    bus.publish("state/res2", {'water_level': 15.0})

    dispatcher.run(current_time=0)

    assert commands["res1"] == rules["profiles"]["flood"]["commands"]["res1_control"]
    assert commands["res2"] == rules["profiles"]["flood"]["commands"]["res2_control"]
    assert dispatcher.active_setpoint_name == "flood"

def test_dispatcher_drought_state(dispatcher_setup):
    """Tests that the dispatcher activates the 'drought' profile when conditions are met."""
    bus, dispatcher, rules, commands = dispatcher_setup

    bus.publish("state/res1", {'water_level': 5.0})
    bus.publish("state/res2", {'water_level': 11.0}) # Drought condition

    dispatcher.run(current_time=0)

    assert commands["res1"] == rules["profiles"]["drought"]["commands"]["res1_control"]
    assert commands["res2"] == rules["profiles"]["drought"]["commands"]["res2_control"]
    assert dispatcher.active_setpoint_name == "drought"

def test_dispatcher_flood_overrides_drought(dispatcher_setup):
    """Tests that the first matching profile in the rule definition wins."""
    bus, dispatcher, rules, commands = dispatcher_setup

    # Both flood and drought conditions are true
    bus.publish("state/res1", {'water_level': 9.5})
    bus.publish("state/res2", {'water_level': 11.0})

    dispatcher.run(current_time=0)

    # Since 'flood' is defined before 'drought' in the rules, it should be active.
    assert dispatcher.active_setpoint_name == "flood"
    assert commands["res1"] == rules["profiles"]["flood"]["commands"]["res1_control"]
    assert commands["res2"] == rules["profiles"]["flood"]["commands"]["res2_control"]
