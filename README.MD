# Big Button

The Kiosk            |  Spaghetti Wiring
:-------------------------:|:-------------------------:
![Picture of the Big Button Kiosk](images/image3.jpeg)  |  ![Picture of the Big Button Kiosk's wiring](images/image1.jpeg)

This is the code for the Big Button Kiosk. It's a sentiment tool where people hit large buttons representing a likert scale.

## Kiosk

This is the code and designs for the physical kiosk. It runs on a Raspberry Pi Pico W.

## Server

This is the code for the backend server that receives button presses and provides an API to interact with it.

### Server Backend

The server backend is written in Rust using the Actix web framework.

### Server Frontend

Current the server frontend is a simple Svelte webpage.