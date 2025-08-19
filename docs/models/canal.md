# Canal Model

The `Canal` model represents a segment of a canal with a trapezoidal cross-section. It simulates water flow using Manning's equation.

## State Variables

-   `volume` (float): The current volume of water in the canal segment (m³).
-   `water_level` (float): The current water level in the canal (m).
-   `outflow` (float): The calculated outflow from the canal for the current time step (m³/s).

## Parameters

-   `bottom_width` (float): The width of the bottom of the canal (m).
-   `length` (float): The length of the canal segment (m).
-   `slope` (float): The longitudinal slope of the canal bed (dimensionless).
-   `side_slope_z` (float): The slope of the canal sides (z in z:1, horizontal:vertical).
-   `manning_n` (float): Manning's roughness coefficient.

## Usage

```python
from swp.simulation_identification.physical_objects.canal import Canal

canal = Canal(
    name="my_canal",
    initial_state={'volume': 100000, 'water_level': 2.1, 'outflow': 0},
    parameters={
        'bottom_width': 20,
        'length': 5000,
        'slope': 0.0002,
        'side_slope_z': 2,
        'manning_n': 0.025
    }
)
```
