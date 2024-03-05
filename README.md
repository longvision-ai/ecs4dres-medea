# MEDEA: A Multi-objective Evolutionary Approach to DNN Hardware Mapping

Multi-Objective Design Space Exploration framework leveraging [Timeloop](https://github.com/NVlabs/timeloop) model.

## Installation
### Docker Compose
```
git clone --recursive https://github.com/Haimrich/medea.git
cd medea/docker
docker-compose run --rm medea
```

### Ubuntu 20.04
Install dependencies
```
sudo apt-get update
sudo apt-get install git build-essential python3-pip cmake libboost-all-dev libconfig++-dev libyaml-cpp-dev 
```
Install [Accelergy](https://github.com/Accelergy-Project/accelergy) v0.3
```
mkdir accelergy; cd accelergy
git clone https://github.com/HewlettPackard/cacti.git
git clone https://github.com/Accelergy-Project/accelergy.git
git clone https://github.com/Accelergy-Project/accelergy-aladdin-plug-in.git
git clone https://github.com/Accelergy-Project/accelergy-cacti-plug-in.git
git clone https://github.com/Accelergy-Project/accelergy-table-based-plug-ins.git
cd cacti; make
cd ../accelergy; git reset --hard 9dc7af1789a96d50a1cad50d9d198bcad759187b; pip3 install .
cd ../accelergy-aladdin-plug-in/; git reset --hard 7fe410252d7aa515ed1d6dc8a29eaa2c4d5f3eaa; pip3 install .
cd ../accelergy-cacti-plug-in/; git reset --hard 643e6fc7635e9f15d0dbd019bc7fb7c8445e7af1; pip3 install .
cp -r ../cacti ~/.local/share/accelergy/estimation_plug_ins/accelergy-cacti-plug-in/
cd ../accelergy-table-based-plug-ins/; git reset --hard 6c5d15dac3491a485f3d8abde2d8596aa1f8221f; pip3 install .

accelergy; accelergyTables
```
Install MEDEA
```
git clone --recursive https://github.com/Haimrich/medea.git
cd medea/build
cmake ..
make
```

## Usage
See the [examples](examples).

## Papers

E. Russo, M. Palesi, S. Monteleone, D. Patti, G. Ascia and V. Catania, "[MEDEA: A Multi-objective Evolutionary Approach to DNN Hardware Mapping](https://ieeexplore.ieee.org/abstract/document/9774747)," 2022 Design, Automation & Test in Europe Conference & Exhibition (DATE)

E. Russo, M. Palesi, D. Patti, S. Monteleone, G. Ascia and V. Catania, "[Multiobjective End-to-End Design Space Exploration of Parameterized DNN Accelerators](https://ieeexplore.ieee.org/abstract/document/9902977)," in IEEE Internet of Things Journal, 2023





