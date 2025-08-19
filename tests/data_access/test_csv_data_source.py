import pytest
from swp.data_access.csv_data_source import CsvDataSourceAgent

# A simple mock for the MessageBus to track publications
class MockMessageBus:
    def __init__(self):
        self.publications = []

    def publish(self, topic, message):
        self.publications.append({'topic': topic, 'message': message})

def test_csv_data_source_agent(tmp_path):
    """
    Tests the CsvDataSourceAgent to ensure it reads a CSV and publishes
    messages at the correct simulation times.
    """
    # 1. Setup: Create a temporary CSV file for the test
    csv_content = "timestamp,inflow,pressure\n10,100,5.5\n20,120,5.8\n30,110,5.7"
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)

    mock_bus = MockMessageBus()
    publish_topic = "test.data.topic"

    # 2. Initialization
    agent = CsvDataSourceAgent(
        agent_id="test_csv_agent",
        message_bus=mock_bus,
        csv_filepath=str(csv_file),
        publish_topic=publish_topic
    )

    # Check if data was loaded correctly
    assert len(agent.data) == 3
    assert agent.last_published_index == -1

    # 3. Execution and Assertion
    # Run at t=0, nothing should be published
    agent.run(current_time=0)
    assert len(mock_bus.publications) == 0

    # Run at t=15, the first row (t=10) should be published
    agent.run(current_time=15)
    assert len(mock_bus.publications) == 1
    publication = mock_bus.publications[0]
    assert publication['topic'] == publish_topic
    assert publication['message']['timestamp'] == 10
    assert publication['message']['value'] == 100
    assert agent.last_published_index == 0 # Index of the row for t=10

    # Run again at t=16, nothing new should be published
    agent.run(current_time=16)
    assert len(mock_bus.publications) == 1

    # Run at t=35, the third row (t=30) should be published (it's the latest one)
    agent.run(current_time=35)
    assert len(mock_bus.publications) == 2
    publication = mock_bus.publications[1]
    assert publication['topic'] == publish_topic
    assert publication['message']['timestamp'] == 30
    assert publication['message']['value'] == 110
    assert agent.last_published_index == 2 # Index of the row for t=30

    # Run at t=35 again, nothing new should be published
    agent.run(current_time=35)
    assert len(mock_bus.publications) == 2
