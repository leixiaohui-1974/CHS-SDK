# Lake Model

The `Lake` model represents a lake or reservoir with a fixed surface area. It accounts for inflow, outflow, and evaporation to track the volume and water level.

## State Variables

-   `volume` (float): The current volume of water in the lake (m³).
-   `water_level` (float): The current water level (m), calculated from volume and surface area.
-   `outflow` (float): The outflow from the lake for the current time step (m³/s). This is determined by downstream demand and set by the simulation harness.

## Parameters

-   `surface_area` (float): The surface area of the lake (m²).
-   `max_volume` (float): The maximum storage capacity of the lake (m³).
-   `evaporation_rate_m_per_s` (float): The rate of evaporation in meters per second.

## Usage

```python
from swp.simulation_identification.physical_objects.lake import Lake

initial_lake_volume = 40e6
lake_surface_area = 2e6

lake = Lake(
    name="my_lake",
    initial_state={'volume': initial_lake_volume, 'water_level': initial_lake_volume / lake_surface_area, 'outflow': 0},
    parameters={'surface_area': lake_surface_area, 'max_volume': 50e6, 'evaporation_rate_m_per_s': 2.31e-8}
)
```
