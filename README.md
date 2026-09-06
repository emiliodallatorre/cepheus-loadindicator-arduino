# Arduino UNO Q Blink Example

Basic blinking LED app to demonstrate how to create projects for the Arduino UNO Q without App Lab.

> ...because I want to develop on a local computer where I have access to my favorite tools, like VS Code, IntelliSense, Copilot, etc.

## Project Structure

UNO Q projects are a little more involved than traditional Arduino (MCU only) projects. They usually combine a Python script for running heavy processing loads (e.g. USB, networking, AI) on Debian Linux on the MPU and a lightweight Arduino sketch that runs on the MCU (for e.g. pin control). This example project contains the following structure:

```sh
q_blink
├── README.md
├── app.yaml
├── python
│   ├── main.py
│   └── requirements.txt
└── sketch
    ├── sketch.ino
    └── sketch.yaml
```

Let's take a look at each of the files:
 * `README.md` is not required, but it's a good thing to have to describe your project and how to run it.
 * `app.yaml` is the App Lab app manifest for the Linux side. It ties the Python entry point (your `python/main.py`), any App Lab “Bricks”/services, and the linkage to the MCU sketch so the App Lab/CLI can build, deploy, and orchestrate both halves together on the UNO Q.
 * `python/main.py` is the Python sketch that runs on the MPU.
 * `python/requirements.txt` lists the Python libraries required for the Python sketch. When you run your project, these libraries will automatically be downloaded and installed.
 * `sketch/sketch.ino` is the Arduino sketch that runs on the MCU.
 * `sketch/skecth.yaml` is the Arduino CLI sketch project file. It declares the board (FQBN), required core/platform versions, libraries, and (optionally) multiple build profiles for reproducible MCU builds.

## Required software

I highly recommend following the directions [here](https://docs.arduino.cc/software/app-lab/tutorials/getting-started/) to install *App Lab* and run it at least once to configure the UNO Q and update the packages/firmware. 

Feel free to look through [these docs](https://docs.arduino.cc/software/app-lab/tutorials/cli/) to see how the CLI commands work, but I'll guide you through the process of sending this project to the UNO Q and running it.

If you are connecting other devices (e.g. webcam) to the UNO Q through a USB hub, you might not be able to communicate to it from your computer via USB (i.e. *adb* might not work). As a result, I recommend using *rsync* to send files from your host computer to the UNO Q. If you're on Windows, I recommend installing and using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) to make life easier (i.e. you have access to `ssh` and `scp` commands).

## Initialize Project

Open a terminal (to be used as your SSH connection to the UNO Q). Enter the following (replace `<UNO_Q_IP_ADDRESS>` with the IP address of your UNO Q board):

```sh
ssh arduino@<UNO_Q_IP_ADDRESS>
```

Enter `yes` if asked to accept the SSH key fingerprint. Enter your UNO Q password.

In that terminal, create a new project folder on the UNO Q:

```sh
mkdir -p ~/ArduinoApps/q_blink
```

## Push Code

From your computer, open up a new terminal, navigate into this directory, and run the following (replace `<UNO_Q_IP_ADDRESS>` with the IP address of your UNO Q board):

```sh
scp -r * arduino@<UNO_Q_IP_ADDRESS>:~/ArduinoApps/q_blink/
```

> **NOTE**: If you're feeling feisty, you could try installing `rsync` on your local machine and on the UNO Q to just update changes. You could also configure `git` on the UNO Q to pull changes from a remote repo. But I'll stick to copying everything with `scp` for now.

## Run the App

Now, we can use the Arduino App CLI to run and control apps. To start your program, run the following in the SSH terminal:

```sh
arduino-app-cli app start ~/ArduinoApps/q_blink
```

Note that Python code prints to logs rather than the console (as the app is run in a container on the UNO Q). To view the logs, run:

```sh
arduino-app-cli app logs ~/ArduinoApps/q_blink
```

Your app runs in the background. You can stop it with:

```sh
arduino-app-cli app stop ~/ArduinoApps/q_blink
```

## VS Code

If you want to easily browse files on the UNO Q, I recommend installing [VS Code](https://code.visualstudio.com/) and the [Remote-SSH extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh). Click on the *Connection* icon in the bottom-left of VS Code and select **Connect to Host...**. Enter `arduino@<UNO_Q_IP_ADDRESS`, select **Linux** when asked about the server's OS, and enter your UNO Q password. You can then select *File > Open Folder...* to get to your *~/ArduinoApps* directory.
