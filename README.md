# plugin-shoebot

This library provides utilities to use shoebot from editors and other programs.


# Plugins

Plugins built with the plugin_shoebot API

## Editor support for shoebot

As well as the Shoebot IDE in the main shoebot repo, plugins are provided:

gedit 3.12 and up.


# API


## Control Shoebot

Run shoebot in a subprocess.


## Communicate with running shoebot

- Pause execution
- Send shoebot code to run
- Quit


## Editor support widgets

### Menus

APIs to create menus

- Examples:  Launch any shoebot example.
- Toggle options: Fullscreen, Show Variables, Enable Livecoding


### Preferences

Store preferences:

- Fullscreen
- Enable Livecoding


### Virtualenvs

- Choose which python environment to run shoebot from.
