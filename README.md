# DeepDip
**DeepDip** is an agent designed to play **no-press Diplomacy** using **Deep Reinforcement Learning** to decide its Orders.

## gym-diplomacy
This repository offers a **new OpenAI Gym environment** to play **no-press Diplomacy**.
* It uses the **BANDANA** framework to set up the rules of the game.
* It uses the architecture of **OpenAI Gym** to make it standard and easily recognizable to any developer.
* It is compatible with the existing agents from **Baselines**.

## Variants
This environment provides three different variants.
* **Standard** - the original Diplomacy map for seven players.
* **Three** - a three-player variant to study how the agent behaves in a multiplayer game.
* **Small** - a two-player variant to understand how the environment works and study the performance of the agent.

## Setup
### Dependencies
Java JDK, Python 2, Python 3, Pipenv.

### Setup Parlance
**Parlance**, the **BANDANA's game engine**, is written in **Python 2**.
The repository provides a **custom version of Parlance** that has additional variants.
The following script install **Parlance** using the version provided in this repository.
```bash
pip2 install -e parlance
```

### Setup BANDANA
**BANDANA** is written in **Java**.
As such, its agents and game engine need to be compiled using **Java JDK**.
It is also recommended to use **Maven** to compile using the provided `bandana/pom.xml` file.
Using the following command will compile the **Java** files.
```bash
mvn -f bandana clean install
```

### Setup Python packages
This project uses **Pipenv** to manage its **Python 3** packages.
First, setup the **new Gym environment** by adding **gym-diplomacy** to **Baselines** setup using the following script.
```bash
echo 'import gym-diplomacy\n' > temp__init__.py
cat __init__.py >> temp__init__.py
mv temp__init__.py __init__.py
```
To install all the necessary packages, you need to set up properly **Pipenv** and run the following command to install the packages of `Pipfile`.
```bash
pipenv install
```

### Setup Protobuf
**Protobuf** establishes the *communication* between **BANDANA's Java** and **Gym's Python**.
You can set it up using the following script.
```bash
cd protobuf
make
cd ..
```

## Usage
### Run the agent
The following script will start the training process of the agent.
```bash
cd deepdip
pipenv run python deepdip_stable-baselines.py
```
It will create a `deepdip-results` folder.
* In `pickles`, it will store the *most recent* and the *best* model.
* The other folders with the name of the algorithm (*PPO2*) will store the **TensorBoard** files.
* The `monitor.csv` files are the records of the training process of the Gym environment.

DeepDip uses the *most recent* model to train, and the *best* model to evaluate itself.
The trained model can be used by changing the `deepdip-results` folder to one of the provided.

At the end of the `deepdip_stable-baselines.py` script, it is generated a graph with the evolution of the rewards.

### Choose Variant Map
The code is using the **Three** variant by default.

To change the variant in use, two alterations on the code must be done.
1. On the **Java**, in the file `TournamentRunner.java`, change the variable `GAME_MAP` to 'standard', or 'small', or 'three'.
2. On the **Python**, in the file `diplomacy_strategy_env.py`, change the variable `CURRENT_MAP` to 'standard', or 'small', or 'three', or to the desired position of the variable `MAPS`.

After these changes, rerun **Maven** to apply the alterations.

## Citation
This work was **my Master Thesis**.

To cite this work in publications:
```
@article{cruz_strategicdiplomacy_2019,
    author = {Cruz, Diogo and {Lopes Cardoso}, Henrique},
    title = {{{Deep Reinforcement Learning}} in {{Strategic Multi-Agent Games}}: the case of No-Press {{Diplomacy}}},
    shorttitle = {{{Deep Reinforcement Learning}} in {{Strategic Multi-Agent Games}}},
    month = jul,
    year = {2019},
    copyright = {openAccess}
}
```

