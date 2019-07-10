# HeCo
*High-resolution heating and cooling profiles based on a lumped-parameters thermodynamic building stock model*

---

## Overview
HeCo is a bottom-up model for the generation of high-resolution (1h, NUTS2) heating and cooling profiles, based on a lumped-parameters thermodynamic model of a given country-wide building stock. The reference building stock is the Italian one, but the model is adaptable to any context.

<img src="https://github.com/SESAM-Polimi/HeCo/blob/master/Regional_heat.jpg" width="500">

The source-code is currently released as v.0.1-pre. This should be regarded as a pre-release: it is not yeat accompained by a detailed documentation, but the Python code is fully commented in each line to allow a complete understanding of it. Further details about the conceptual and mathematical model formulation are provided here: https://doi.org/10.18280/ti-ijes.632-434. 

Please consider that a newer, fully commented and more user friendly version is under development and should be released soon.

The repository also hosts all the input files used to generate the profiles appearing in the abovementioned study, which may be also used as a reference example. 

## Requirements
The model is developed in Python 3.6, and requires the following libraries:
* numpy
* matplotlib
* math
* random

## Quick start
[...]

## Authors
The model has been developed by:

**Francesco Lombardi, Matteo Vincenzo Rocco, Simone Locatelli, Chiara Magni, Emanuela Colombo** <br/>
Politecnico di Milano, Italy <br/>
E-mail: francesco.lombardi@polimi.it <br/>

**Lorenzo Belussi, Ludovico Danza** <br/>
Construction Technologies Institute - National Research Council of Italy (ITC-CNR), Italy <br/>

## Citing
Please cite the following publication if you use HeCo in your research:
*F. Lombardi, M.V. Rocco, S. Locatelli, C. Magni, E. Colombo, L. Belussi, L. Danza, Bottom-up Lumped-parameters Thermodynamic Modelling of the Italian Residential Building Stock: Assessment of High-resolution Heat Demand Profiles, Tecnica Italiana-Italian Journal of Engineering Science, 2019, https://doi.org/10.18280/ti-ijes.632-434.*

## Contribute
This project is open-source. Interested users are therefore invited to test, comment or contribute to the tool. Submitting issues is the best way to get in touch with the development team, which will address your comment, question, or development request in the best possible way. We are also looking for contributors to the main code, willing to contibute to its capabilities, computational-efficiency, formulation, etc. 

## License
Copyright 2019 HeCo, contributors listed in **Authors**

Licensed under the European Union Public Licence (EUPL), Version 1.1; you may not use this file except in compliance with the License. 

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License
