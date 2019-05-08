# gym-diplomacy

This folder contains the adapted environment of Diplomacy.

It is important to note that it **does not** follow the Open AI Gym environments framework.

In an Open AI Gym environment, the action is **taken by the agent whenever he wants to act**. However, because this is a port of the BANDANA framework for Diplomacy, a BANDANA agent can only act when the BANDANA game says so, we have **the environment deciding when the agent shall act**.

This "pseudo-environment" is still based on Open AI Gym and it uses its Spaces, but it cannot be used as a regular Open AI Gym environment.

Instead of an agent building up the environment, the environment builds agents and calls them to act.

## Getting started

### Prerequisites

TODO

### Installing

First you'll need to install the package containing the environment. Run the following command in the root of this repository:

`pip install -e .`

This will use the `setup.py` file to install the `gym-diplomacy` environment.

In order to use the environment as a regular OpenAI Gym environment, it needs to be registered in the `gym` package. This registration is called on the `__init__.py` file of the environment package.


To do so, simply add the following line to the agent you're executing:

`import gym_diplomacy`

**Even if you don't call `gym_diplomacy` explicitly, this line needs to be there to execute the registration.**