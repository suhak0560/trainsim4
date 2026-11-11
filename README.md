# trainsim4
**A lightweight train performance simulation tool written in Python**

**trainsim4** is a lightweight, Python-based tool for exploring and studying train performance through numerical simulation.

This project is designed primarily for **research, education and recreation**, providing an accessible environment for experimenting with train and route characteristics and investigating simulated train behaviour.
## Intended use and safety disclaimer
This project is developed for **research, educational and recreational purposes**, including academic studies, numerical modelling, simulation development and games.

This project is not certified, approved or validated for safety-critical railway applications. It is not intended to be relied upon for real-world railway operations, safety-critical decisions, or regulatory compliance and certification.

This project may contain simplified physical models, numerical approximations, and assumptions that do not fully represent actual railway conditions. Simulation results should not be considered authoritative for operational or regulatory purposes.
## Features
This project provides a Python-based framework for train performance simulation.

This repository includes the following components:

- **Main entrance (`main.py`)**: Entry point for running the program
- **Train editor (`traineditor.py`)**: Train-related configuration functionality
- **Route editor (`routeeditor.py`)**: Route-related configuration functionality
- **Train simulation module (`trainlib.py`)**: Supporting train-related code
- **Input module (`inputs.py`)**: Input definitions and related functionality

## Environment requirements
- Python 3.8 or later
- Additional Python dependencies: `pandas` and `scipy`
## Installation
Download ZIP and unzip the files into the same directory.

Ensure that Python 3.8 or later is installed and that any required dependencies are available.
## Quick start
Run the main application:

```python main.py```

Follow the interactive prompts to select the desired operation and provide the required data.
## Inputs and outputs
(to be supplemented)
## Modelling approach
(to be supplemented)
## Examples
(to be supplemented)
## Model scope & limitations
This project is designed to simulate train performance under simplified operational conditions, primarily focusing on train movement within the **constant-power region** of the traction characteristics.
### Supported railway systems
This project is suitable for simulating the following types of railway systems, provided that their operating characteristics are consistent with the model assumptions:
- **Conventional wheel-rail trains** including multiple units, loco-hauled trains, freight trains, etc., whether they are electric-powered or diesel-powered, single-decker or double-decker
- **Maglev trains**
- **Rubber-tyred light metro trains**
### Traction and low-speed performance
This project primarily models train performance within the constant-power region, where tractive effort is determined by the available traction power and train speed.

Low-speed operational performance is specified by the user during the train creation workflow, rather than being calculated in detail by the simulation model.

The simulation assumes that trains have reached at least their **base speed** after departing a station and remain at or above their base speed until approaching the next station.

Consequently, the model is most appropriate for railway systems where the constant-power region represents a significant portion of normal train operation.
### Excluded application
This project is not designed for:
- **Mixed road traffic** including trams, light rail or other vehicles operating in mixed road traffic, where interactions with road users and traffic conditions affect vehicle movement
- **Predominately low-speed operation** including shunting movement or other operational scenarios primarily below their base speed, where low-speed traction characteristics dominate their performance
- **Detailed low-speed analysis** including heavy-haul trains which cannot reach their base speed after departing a station that requiring explicit modelling of traction behaviour below base speed, beyond the performance characteristics provided by the user
- **Cable transport** and other modes whose motion relies on external forces
### General modelling assumptions
Simulation results depend on the accuracy of user-provided train and route parameters and the applicability of the simplified mathematical model.

The model's assumptions should be considered when interpreting results, particularly for vehicles or operating conditions that differ significantly from those described above.

For information regarding safety certification and permitted applications, refer to the **Intended use and safety disclaimer** section.
## Repository structure
```
trainsim4/
├── main.py
├── inputs.py
├── routeeditor.py
├── traineditor.py
├── trainlib.py
├── README.md
└── LICENSE
```
## Contributing
Suggestions, bug reports, documentation improvements and contributions are welcome through GitHub Issues and Pull Requests.

Contributors are encouraged to document any new modelling assumptions, dependencies or limitations introduces by their changes.
## License and warranty
This project is distributed under the [MIT License](https://github.com/suhak0560/trainsim4?tab=MIT-1-ov-file), which permits use, copying, modification and redistribution, subject to its terms.

This software is provided **"AS IS"**, without warranty of any kind. The MIT License includes provisions disclaiming warranties and limiting the liability of authors and copyright holders.

The safety disclaimer above describes the intended application and certification status of this project. It does not alter or restrict the permissions granted under the MIT License.
## Citation
If you use this project in research or educational materials, please acknowledge the project and link to the repository:

[https://github.com/suhak0560/trainsim4](https://github.com/suhak0560/trainsim4)
