# Vundu_lab V0.1.0       [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/MindFarter/Vundu_lab)

One local tool that takes an ESP32 project export from a folder to a running
board: **Compile** it, **Flash** it, and **Monitor** it, all in one window, all
on your own computer. It is not tied to one design tool: it compiles any
PlatformIO project (a folder with a `platformio.ini`) or Arduino sketch for an
ESP32-family board. Vundu_lab is for ESP32 boards only for now. It has been tested
on **one** real board, an ESP32-C6, using an LCD Wizard export; the 
[Supported boards and chips](#supported-boards-and-chips) section says exactly
what has and has not been tested.

Vundu_lab is a wizard and nothing more. It contains no compiler, no build system
and no flasher of its own. The real work is done by open-source projects built
by other people (PlatformIO, pioarduino, Arduino CLI, esptool and pyserial),
and all credit belongs to them. See 
[Credits and licences](#credits-and-licences).

This release (V0.1.0) has five tabs: **Compile**, **Monitor**, **Plot**, **Flash**
and **Modbus**, and checks its own tools every time it starts. The Compile,
Monitor and Flash tabs have been tested on a real board (an ESP32-C6). **Plot**
and **Modbus** are the newest tabs: they have been tested against the built-in
demo device, and testing on real hardware is still to come.

Vundu_lab has a dark theme (background `#141414`, highlights `#FFCC14`) and was
called Firmware Wizard until V0.0.6. Project page: 
<https://github.com/MindFarter/Vundu_lab>

- - -
## The workflow

1.  **Compile tab.** Click **Open Folder** and choose your project folder (an
    ESP32 project export, for example). Pick an engine (PlatformIO, pioarduino
    or Arduino IDE) and click **Compile**. **Stop** cancels at any time.
2.  **Send to Flash.** When the compile succeeds, click **Send to Flash** next to
    the finished file. It jumps to the Flash tab with the file already loaded
    and its address filled in. (Download and Save to folder are still there in
    the Compile tab if you want the file itself.)
3.  **Monitor tab.** Check the port in the sidebar and click **Connect**, then
    go to the Flash tab.
4.  **Flash tab.** Select the correct baud rate, click **Detect chip**, then
    click **Flash firmware**.
5.  **Monitor tab.** When flashing finishes, the Monitor opens by itself and
    shows the board’s boot messages.

The **Monitor**, **Plot**, **Flash** and **Modbus** tabs share a connection
sidebar, and their layout is modelled on LCD Wizard’s SerialWizard (see *Credits*
). The Compile tab has no connection settings, because it does not need a board.

- - -
## Running it

You need Python 3.9 or newer. There is nothing to `pip install` yourself.

```
cd Vundu_lab_V0.1.0
python3 vundu_lab.py
```
It opens in your browser, normally at `http://127.0.0.1:8765`. If that port is
busy it uses the next free one and prints the address. Press `Ctrl+C` in the
terminal to stop it.

On Ubuntu and Debian, install two extra packages once:

```
sudo apt install python3-venv python3-tk
```
When it starts, it prints a short [start-up check](#start-up-check) of
everything it depends on. The first compile with each engine downloads that
engine and your board’s toolchain, so it is slow once. The first time you open
Flash or Monitor, press **Install (one-off)** to fetch the serial tools. Internet
is needed for those downloads only.

- - -
## Start-up check

Every time the server starts it checks the things it depends on but does not
ship, and prints one short block in the terminal before the address. Each
problem comes with the exact command to fix it, so you find out in seconds
instead of after a compile and a flash attempt. A problem never stops the app
from starting.

```
Vundu_lab V0.1.0 - start-up check
  Python 3.12.3 .......................... ok
  Virtual environments (venv + pip) ...... ok
  Folder dialog (tkinter) ................ ok
  pyserial (Monitor, Plot, Modbus) ....... ok
  esptool (Flash) ........................ MISSING
      -> not installed in /home/you/Vundu_lab_V0.1.0/data/engines/serial/venv
      -> open the Monitor or Flash tab and press Install (one-off)
      -> or in a terminal:  <the exact command, quoted for your path>
  PlatformIO engine ...................... installed
  pioarduino engine ...................... not installed yet
      -> the first Compile with it installs it (needs internet)
  Arduino CLI engine ..................... installed
  Serial port access (dialout group) ..... ok
  1 item(s) need attention (see the -> lines). The app still starts.

|```
                    |Line                |What it checks                                                |If it is missing                                                             |
|--------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------|
|Python              |Version 3.9 or newer                                          |Install a newer Python.                                                      |
|Virtual environments|The `venv` and `ensurepip` parts of Python, which the engines need|`sudo apt install python3-venv`                                              |
|Folder dialog       |`tkinter`, used by Open Folder and Save to folder             |`sudo apt install python3-tk` (without it you paste folder paths instead)    |
|pyserial, esptool   |Both are really inside `data/engines/serial/venv`             |Press **Install (one-off)** in the Monitor or Flash tab, or run the command shown|
|The three engines   |Whether each is installed yet                                 |Not a problem: the first Compile with it installs it                         |
|Serial port access  |(Linux) that you are in the `dialout` group                   |`sudo usermod -aG dialout $USER`, then log out and back in                   |
|Internet            |Only checked when something needs downloading                 |Connect first. The engines and serial tools are downloaded.                  |

A renamed engine folder is put back automatically (see *Where everything lives*
). If that cannot be done safely, the check says **WRONG FOLDER** and tells you
what to rename.

- - -
## Supported boards and chips

Vundu_lab works by **chip**, not by board. The chip decides which device the Flash
tab talks to and which board name your project uses, so any board built around
one of the ESP32 chips below should behave the same way. Vundu_lab is for **
ESP32-family boards only** for now.

### What has been tested


|What                                                                                      |How it was tested                                      |Result                                                                            |
|------------------------------------------------------------------------------------------|-------------------------------------------------------|----------------------------------------------------------------------------------|
|**Compile, Flash and Monitor** on a **Waveshare ESP32-C6-Touch-LCD-1.47** (ESP32-C6, built-in USB)|On the real board, with an LCD Wizard export           |Worked: it compiled, flashed, and the Monitor showed the board’s output afterwards|
|**Plot** and **Modbus**                                                                   |Simulated data and the built-in Modbus demo device only|Worked in those tests. Not yet tried on real hardware                             |
|**Everything else in this section**                                                       |Not tested                                             |Set up and expected to work, but nobody has tried it yet                          |

So **one board has been tested on real hardware.** Everything else below is set
up in the code and should work, but please treat it as untested until it has
been tried.

### Flash tab: the chips


|Chip            |In the Flash tab          |Status                                                                                                                                           |
|----------------|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
|ESP32-C6        |Button                    |**Tested** (see above)                                                                                                                           |
|ESP32 (original)|Button                    |Not tested                                                                                                                                       |
|ESP32-S3        |Button                    |Not tested                                                                                                                                       |
|ESP32-C3        |Button                    |Not tested                                                                                                                                       |
|ESP32-C5        |Button                    |Not tested                                                                                                                                       |
|ESP32-P4        |Button                    |Not tested. Vundu_lab flashes the P4 only. If the board has a separate ESP32-C6 for Wi-Fi, updating that C6 is a different job that Vundu_lab does not do|
|ESP32-C2        |Button                    |Not tested. See the note about C2 and H2 under *What compiles from what*                                                                         |
|ESP32-H2        |Button                    |Not tested. Same note                                                                                                                            |
|ESP32-S2        |No button: use **Auto-detect**|Not tested                                                                                                                                       |

Flashing is done by `esptool`, so the real limit is whatever the installed
version of `esptool` supports.

### Boards by chip

These examples come from LCD Wizard’s public list of board presets (
[lcdwizard.com/boards](https://lcdwizard.com/boards), 125 boards when it was
checked in November 2026). Every ESP32-family board on that list uses one of
the chips above, so Vundu_lab should handle it. It is a list of examples, not a
promise: apart from the one board above, none has been tested.


|Chip            |Example boards                                                                                                                                                                                                                                                                                                       |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**ESP32-C6**    |Waveshare ESP32-C6-Touch-LCD-1.47 (**tested**), and the Waveshare ESP32-C6 LCD, Touch-LCD and Touch-AMOLED boards (for example C6-GEEK, LCD-1.28, Touch-LCD-2.8, Touch-AMOLED-1.8)                                                                                                                                   |
|**ESP32**       |ESP32-2432S028R “Cheap Yellow Display” and its variants, Guition JC2432W328R and C, LCDWIKI 2.8" and 4.0" ESP32-32E, WT32-SC01, M5Stack Core2 (v1.0 and v1.1), Waveshare ESP32-Touch-LCD-3.5, and ordinary ESP32 DevKit boards                                                                                       |
|**ESP32-S3**    |Sunton ESP32-8048S043 and S070, WT32-SC01 Plus, LilyGO T-Display-S3 and its AMOLED version, Guition JC3248W535, JC4827W543C and 4848S040, VIEWE UEDX48480040E-WB-A, LCDWIKI ES3C28P, ES3C35P and ES3C40P, a large range of Waveshare ESP32-S3 Touch-LCD and Touch-AMOLED boards, and ordinary ESP32-S3 DevKitC boards|
|**ESP32-C3**    |Waveshare ESP32-C3-LCD-1.47                                                                                                                                                                                                                                                                                          |
|**ESP32-C5**    |RockBase IoT NM-CYD-C5, and the Waveshare ESP32-C5 LCD-1.47, LCD-2.73 and Touch-LCD-1.69, 2.8 and 3.5                                                                                                                                                                                                                |
|**ESP32-P4**    |Waveshare ESP32-P4-WIFI6-Touch-LCD boards and ESP32-P4-NANO with DSI touch screens, Elecrow CrowPanel Advanced 7, 9 and 10.1 inch, VIEWE ESP32-P4 SmartDisplay 7 inch, Guition JC1060P470C and JC8012P4A1, M5Stack Tab5                                                                                              |
|**ESP32-S2, C2, H2**|LCD Wizard has no presets for these. Vundu_lab can flash them in principle, but nothing has been tried                                                                                                                                                                                                                   |

### Boards with a USB-to-serial chip

Some boards reach the chip through a separate USB-to-serial chip instead of the
chip’s own USB. One example is the **Waveshare ESP32-S3-Pico** (an ESP32-S3 with
16 MB flash and 2 MB PSRAM, a CH343P serial chip and BOOT and RESET buttons,
according to the retailer’s product page). **It has not been tested.** On a board
like this:

- The automatic reset (**Auto (DTR/RTS)**) may not work. If Detect chip or Flash
  fails, choose **Hold BOOT** in the Flash tab: hold the BOOT button, tap RESET,
  then press Flash.
- Serial output comes through the serial chip, so the Monitor should work at
  115200 as long as the firmware’s “USB CDC on boot” setting is off.
- With the Arduino engine, the board-name guess may wrongly pick a Raspberry Pi
  Pico because the name contains “pico”. Type `esp32:esp32:esp32s3` (plus any
  PSRAM and flash options) in the **Arduino board** box.

### Not supported yet

- **Raspberry Pi Pico boards** (RP2040, and the RP2350 in the Pico 2 and Pico 2
  W), **Arduino AVR boards** (Uno, Nano, Mega), **Arduino Uno R4**, **STM32** and **
  ESP8266**. The Arduino engine has the RP2040 and STM32 board sources
  configured, so a sketch for those might compile, but the Flash tab cannot
  write them, so they are not supported.
- Updating the ESP32-C6 companion chip on ESP32-P4 boards.
- Debug probes (JTAG).

- - -
## Connection sidebar (Monitor, Plot, Flash and Modbus)

- **Port.** Only real USB serial devices (your board) are listed, one board at a
  time. Legacy built-in ports such as `ttyS0` are hidden. If the list says *No
  board detected*, plug the board in and press the refresh button.
- **Settings.** Baud rate, data bits, parity, stop bits, flow control, DTR and
  RTS, and an **Auto-reconnect** switch. The last port and baud are remembered.
- **Traffic.** Live RX and TX byte counts and a bytes-per-second graph.
- **Serial tools.** The first time, a message offers **Install (one-off)**. When
  it finishes it says the tools are installed and then disappears.

## Monitor

- **Views.** Text, ASCII, Hex, Hex+ASCII, Dec and Bin. Switching redraws
  everything already received.
- **View options.** Timestamps, show sent data, obey clear-screen codes, freeze
  view, bytes per line, packet gap (a new line when data pauses for that long)
  and font size.
- **Send** as text or hex with a line ending of your choice (LF, CR, CR+LF or
  none). Up and down arrows recall earlier lines.
- **Search, Clear, Copy** and **Export transcript** (a `.txt` of what the window
  shows). `Ctrl+L` also clears.
- **Auto-reconnect.** If the board resets or is unplugged, the Monitor keeps
  retrying and picks the port up again.

## Flash

- **Target.** Choose the chip or leave it on Auto-detect, set the flash baud, and
  choose how to enter the bootloader: **Auto (DTR/RTS)**, or **Hold BOOT** for
  boards with no auto-reset (hold BOOT, tap RESET, then flash). **Detect chip**
  asks the board which chip it is.
- **Firmware.** Add `.bin` files with **Send to Flash**, by dropping them on the
  page, or by clicking to browse. Each file is recognised from its **contents**,
  not its name: merged image, bootloader, partition table, `boot_app0` or app.
  It gets the right flash address and chip, shown beside it. Addresses can be
  edited, and each file has an on/off switch.
- **Safety check.** Files that would overlap in flash are refused before anything
  is written.
- **The Monitor is switched off while the Flash tab is open**, so the two can
  never fight over the USB port. The Connect button is greyed out with a note.
  Leaving the Flash tab switches the Monitor back on (reconnecting if it was
  connected), and so does finishing a flash with *Open the serial monitor when
  done* ticked.
- **Flashing.** The server closes its own copy of the port, runs `esptool`,
  shows progress and a log, then reopens the port. **Verify with MD5** can be
  switched off, **Open the serial monitor when done** switches to the Monitor,
  and **Cancel** stops a flash in progress.
- Supported chips are whatever the installed `esptool` supports, which includes
  the ESP32, S2, S3, C2, C3, C5, C6, H2 and P4.

## Plot

*Status: tested with simulated data and with values from the Modbus demo device.
Testing on real boards is still to come.*

The Plot tab draws numbers from whatever your board prints, with no setup.
Values are picked out of each line automatically, in three formats:


|Your board prints             |Result                                                                    |
|------------------------------|--------------------------------------------------------------------------|
|`temp:23.5, hum:41%`          |Named series (`temp`, `hum`)                                              |
|`23.5 41 1013.2`              |Plain columns (`ch1`, `ch2`, `ch3`)                                       |
|`time,volts,amps` then `0,3.3,0.5`|A header line names the columns that follow. A `time` column is not plotted.|

In Arduino code, `Serial.printf("temp:%.1f,hum:%d\\n", t, h);` produces the
first format. Ordinary log lines such as boot messages are ignored.

- **Range:** 10 s, 30 s, 1 m, 5 m or All.
- **Layout:** **Overlay** puts every series on one chart, **Split** gives each
  its own lane, and **Auto** splits series that sit at very different levels (for
  example temperature near 20 and pressure near 1000) and overlays the rest.
- **Pause** freezes the picture (data keeps arriving). **✕** clears everything.
- **Record** starts a fresh capture that is kept in full (up to 200,000 samples)
  so you can export a long run. Without it the newest 30,000 samples are kept.
- **CSV** saves the data. **PDF** opens a report page with the chart and a min,
  max and mean table, and the print dialog appears so you can choose *Save as PDF*
  . Your browser may ask you to allow pop-ups.
- Values read on the Modbus tab can be sent here too.

## Modbus

*Status: tested against the built-in demo device. Testing on real RTU and TCP
devices is still to come.*

A Modbus master for RTU (over the serial port in the sidebar) and TCP.
Addresses are the **0-based protocol addresses**, so holding register 40001 is
address 0.

- **Link.** Choose RTU or TCP (host and port), the reply timeout and how often to
  poll. RTU uses the sidebar port and settings and connects it for you if
  needed. While RTU runs, the Monitor only sees data that is not a Modbus reply.
- **Reads.** Add as many as you like, each with unit, function (01 coils, 02
  discrete inputs, 03 holding, 04 input), start address, count, a type (U16,
  S16, U32, S32, F32, Hex or Binary), a word order (ABCD, CDAB, BADC or DCBA),
  a name and a scale. 32-bit types use two registers per value. **Read once** or **
  Start polling**. **Send values to the Plot tab** plots every numeric value
  under its name.
- **Write.** Register 06 (one register), Registers 16 (several), Coil 05 and
  Coils 15. Type values like `1234`, `0x04D2`, `\-5` or `12.5`, and choose how
  to encode them (type and word order). Coil values are `1`, `0`, `on` or `off`.
- **Results.** Request, OK and error counts, the average round trip, a table of
  address, name, raw value and decoded value, and a `traffic.log` of the exact
  frames (with CRC and Modbus exception errors explained).
- **Demo device.** On the TCP link, **Start demo device** runs a small pretend
  Modbus device inside Vundu_lab so you can try everything with no hardware:
  register 0 is a counter, register 1 a sine wave, registers 2 and 3 a 32-bit
  float temperature (ABCD), and everything else is writable memory.

## Ports and safety

- **Web server port.** If 8765 is busy, the next free port (up to 8784) is used.
  On Windows the server also refuses to share a port with another program.
- **Serial ports.** Only one program can hold a serial port at a time, so close
  other monitors first. On Linux, your account must be in the `dialout` group (`
  uucp` on Arch): Vundu_lab detects this and shows the exact command.
- **Security.** The server listens only on `127.0.0.1`. Every request needs a
  random token created each time the server starts and given only to its own
  page, and requests from other websites are rejected. Anything that changes
  state or touches hardware (connecting, sending, flashing, uploading) is a
  POST request. The server only reads files inside the folder you opened.

- - -
## Where everything lives

Everything Vundu_lab installs is inside its own folder, in `data/engines/`. Each
engine has **one** folder with **one** Python environment (`venv`), and nothing
else is ever created:


|Folder                  |What it is                                                   |Created by                  |
|------------------------|-------------------------------------------------------------|----------------------------|
|`data/engines/platformio/`|PlatformIO                                                   |the first PlatformIO compile|
|`data/engines/pioarduino/`|pioarduino                                                   |the first pioarduino compile|
|`data/engines/arduino/` |Arduino CLI                                                  |the first Arduino compile   |
|`data/engines/serial/`  |pyserial and esptool, used by Monitor, Plot, Flash and Modbus|the **Install (one-off)** button|

- **Never rename these folders.** Each environment remembers its own location, so
  a renamed one breaks. On start-up Vundu_lab checks them, and if an engine folder
  was renamed to `serial` it puts it back.
- **Installed means installed here.** Monitor and Flash only count as ready when `
  data/engines/serial/venv` really contains both `pyserial` and `esptool`. A `
  pyserial` installed somewhere else on your computer is deliberately ignored,
  so the flasher can never be silently missing.
- **Checking by hand.** Run these from the Vundu_lab folder (on Windows use `
  data\\engines\\serial\\venv\\Scripts\\python`):

  ```
  data/engines/serial/venv/bin/python -m esptool version
  ```
- **Spaces in the folder path need quotes** in a terminal, or the command is read
  as two words and fails with “No such file or directory”:

  ```
  cd "/home/you/My Projects/Vundu_lab_V0.1.0"
  ```
  The commands Vundu_lab shows in its logs are already quoted, so you can copy them
  as they are.

- **Save to folder** opens a folder dialog that starts in your Downloads folder.
  Choose where the file should go.

- - -
## What compiles from what

This describes exactly what the code does, so you can judge what will and will
not work.

### The three engines


|Engine            |What it needs in your folder                                        |What it runs                                |What it compiles                                                                                                                  |
|------------------|--------------------------------------------------------------------|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
|**PlatformIO**    |A `platformio.ini`                                                  |`pio run` in its own environment            |Whatever platform and board the `platformio.ini` names. The platform, toolchain and libraries it lists are downloaded the first time|
|**pioarduino**    |A `platformio.ini`                                                  |The same, using a temporary copy of the file|The same project, built with the pioarduino ESP32 platform (a newer Arduino-ESP32) instead of the standard one                    |
|**Arduino IDE** button|A sketch folder holding a `.ino` file with the same name as the folder|`arduino-cli compile`                       |The sketch, for the board named in the **Arduino board** box                                                                      |

- **How pioarduino swaps the platform.** Vundu_lab writes a temporary file called `
  .cw_pioarduino.ini` in your project folder, changes any line that says `
  platform = espressif32` (with or without a version) to point at the pioarduino
  platform’s stable release, builds with that file, and deletes it afterwards.
  Lines that already point somewhere else are left alone. Your own `
  platformio.ini` is never edited.
- **Libraries.** If your folder has a `LIBRARIES.md` (LCD Wizard exports do),
  every line in it that starts with `arduino-cli lib install` is run before the
  Arduino engine compiles. Libraries for other projects are not installed
  automatically. PlatformIO installs the libraries listed in your `platformio.ini`
  by itself.

### Choosing the Arduino board name

The Arduino engine needs a full board name (called an FQBN). Vundu_lab guesses one
from your `platformio.ini` and puts it in the box, and you can change it:


|If the board name in platformio.ini contains…    |Vundu_lab guesses                                               |Supported?           |
|-------------------------------------------------|------------------------------------------------------------|---------------------|
|`p4`, `c6`, `c5`, `c3`, `s3` or `s2`             |`esp32:esp32:` plus that chip, for example `esp32:esp32:esp32s3`|Yes                  |
|none of the above                                |`esp32:esp32:esp32`                                         |Yes                  |
|`pico` or `rp2040`                               |`rp2040:rp2040:rpipico`                                     |No: cannot be flashed|
|`stm32` (anywhere in the file), `nucleo` or `blackpill`|`STMicroelectronics:stm32:GenF4`                            |No: cannot be flashed|

- **The checks run in this order:** `pico` or `rp2040` first, then STM32, then
  the ESP32 chips. So an ESP32 board whose name contains “pico” (for example an
  ESP32-S3-Pico) is wrongly guessed as a Raspberry Pi Pico. This only affects
  the Arduino engine: type the right name in the box, for example `
  esp32:esp32:esp32s3`.
- The guess only picks the **chip family**. Options such as PSRAM, flash size and
  partition scheme are not set, so add them to the end of the name if your
  board needs them (Arduino CLI accepts options in the name).
- **ESP32-C2 and ESP32-H2 are not recognised** from the board name, so they are
  treated as a plain ESP32. This matters in one place: if the platform does not
  build its own complete `firmware.factory.bin`, the one Vundu_lab builds would use
  the wrong bootloader address for those two chips. For C2 and H2, rely on the
  platform’s own complete file, or flash the separate files at their addresses.
- The board’s **core** is installed from the first two parts of the name. Vundu_lab
  knows three extra board sources (Espressif’s ESP32 index, Arduino-Pico and
  STM32duino) and also uses Arduino’s own default list. Everything is installed
  inside the Vundu_lab folder.

### The files Vundu_lab offers


|Engine                   |Files offered after a successful compile                                                                                                       |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
|PlatformIO and pioarduino|From `.pio/build/\<environment>/`: `firmware.factory.bin` (the complete image, flashed at `0x0`), then `firmware.bin`, `bootloader.bin` and `partitions.bin`|
|Arduino                  |From `.cw_build/`: `\<sketch>.ino.merged.bin` first (the complete image), then the other `.bin` files                                          |

If the platform builds `firmware.factory.bin` itself, that is the file offered.
If it does not, and there is a `bootloader.bin`, Vundu_lab builds the complete file
with `esptool`: the chip comes from the board name, the bootloader goes at `
0x1000` (ESP32, S2), `0x0` (S3, C3, C6) or `0x2000` (C5, P4), the partition
table at `0x8000`, `boot_app0` at `0xe000` and the app at `0x10000`.

### What the Flash tab recognises

When you add a `.bin` file, the Flash tab reads its **contents**, not its name,
and sets the flash address for you. It recognises a complete (merged) image, a
bootloader, a partition table, `boot_app0` and an app image, and it reads the
chip from the image header. This covers all nine chips: ESP32, S2, S3, C2, C3,
C5, C6, H2 and P4.

- - -
## How Compile works

### One package, nothing scattered

Everything the engines need is kept inside the Vundu_lab folder:

```
Vundu_lab_V0.1.0/
  vundu_lab.py       the local server
  index.html         the interface
  README.md          this file
  vundu_logo.png     the logo
  LICENSE            the MIT licence
  data/engines/
    platformio/      its own Python environment and its own core folder
    pioarduino/      its own Python environment and its own core folder
    arduino/         arduino-cli with its own data, libraries and downloads
    serial/          pyserial and esptool, in their own environment
  data/uploads/      .bin files you drop on the Flash tab
  data/settings.json your last port and baud rate
```
Nothing is installed into `~/.platformio`, the Arduino folders in your home
directory, or VS Code. If you already use any of those, Vundu_lab will not touch or
conflict with them. To remove everything, delete the folder.

### Why PlatformIO and pioarduino can run side by side

pioarduino is built on the PlatformIO core, and the two share a lot, which is
exactly why they clash when installed together. Vundu_lab gives each one a
completely separate Python environment and a separate core folder, so they
behave as two independent programs.

For **pioarduino**, Vundu_lab builds from a temporary copy of your `platformio.ini`
in which the ESP32 platform line points at pioarduino’s platform. Your own
files are never edited, and the temporary copy is deleted afterwards.

### The Arduino IDE button

This button runs **Arduino CLI**, the command-line engine that the Arduino IDE
itself is built on, rather than opening the IDE’s window. It installs the board
support for the board you choose, installs the libraries listed in the export’s `
LIBRARIES.md`, then compiles the sketch. The board is guessed from your `
platformio.ini` and shown in a text box (an FQBN such as `esp32:esp32:esp32s3`)
that you can edit.

### What happens when you press Compile

1.  The server starts the chosen engine as a separate process, using only that
    engine’s own folders.
2.  Everything the engine prints is streamed to the output viewer as it happens.
3.  If it succeeds, the server looks for the finished files in the hidden build
    folder (`.pio/build/…` for PlatformIO and pioarduino, `.cw_build` for
    Arduino).
4.  For ESP32 boards it offers the complete `firmware.factory.bin` if the
    platform built one. If not, it uses `esptool` (supplied by PlatformIO) to
    merge the bootloader, partition table and firmware into one file.

### The files you get


|File                          |What it is                                                                                                                                                               |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|`firmware.factory.bin`        |The easiest option for ESP32 boards. One complete file, flashed at address `0x0`. Vundu_lab uses the one the platform builds itself, and only makes its own if there isn’t one.|
|`\<Sketch>.ino.merged.bin`    |The same kind of complete file from the Arduino engine.                                                                                                                  |
|`firmware.bin`                |The application only. Needs the bootloader and partition table too.                                                                                                      |
|`bootloader.bin`, `partitions.bin`|The other pieces, for flashing by hand at their own offsets.                                                                                                             |

Downloaded or saved files are prefixed with the project name so they are easy
to tell apart.

### Safety (see also Ports and safety below)

The server only listens on your own computer (`127.0.0.1`) and rejects requests
that do not come from its own page. It only reads files inside the folder you
opened.

- - -
## How it is built

Vundu_lab is two files plus this README, the logo and the licence. There is nothing
to compile.


|File        |What it is                                                                                            |
|------------|------------------------------------------------------------------------------------------------------|
|`vundu_lab.py`|The local server. Python standard library only.                                                       |
|`index.html`|The whole interface: HTML, CSS and JavaScript in one file, with no outside libraries or network calls.|

**The server** uses Python’s built-in threaded HTTP server. Engines run as
separate processes, and their output is streamed to the page with server-sent
events. Compile output uses one stream per compile. Serial data, flash progress
and setup messages share one long-lived stream (`/api/events`).

**Engines** are kept apart so nothing conflicts. PlatformIO and pioarduino each
get their own Python environment and core folder, `arduino-cli` has its own
folders, and the serial tools have their own environment. All of it lives in `
data/engines/` and is created on first use.

**Serial** uses `pyserial`, installed into `data/engines/serial/`. The server
adds that folder to its import path and reads the port in a background thread.
Flashing runs `esptool` as a separate program, after the server has released the
port. Flash files are recognised by reading the image headers (merged image,
bootloader, partition table, `boot_app0` or app), not by file name. While the
Flash tab is open the server keeps the port free (the Monitor is switched off),
so only one program ever uses it.

**Modbus** is written from the public Modbus specification, with no Modbus
library. The browser builds each request and decodes each reply; the server
wraps it in an RTU frame (with CRC-16) or a TCP frame, sends it and returns the
raw reply. A lock makes sure the Monitor’s reader and a Modbus transaction
never use the serial port at the same moment. TCP opens a short connection per
request, and the demo device is a small socket server inside the same program.

**The start-up check** (`startup_report()`) uses only the standard library: it
looks for the `venv`, `ensurepip` and `tkinter` modules, looks inside `
data/engines/` for each engine’s files, checks your group membership, and only
tries to reach the internet when something needs downloading (with a 2 second
limit). It runs once, before the server starts, and any failure inside it is
caught so it can never stop the app.

**The interface** talks to the server with plain `fetch` calls. A small wrapper
adds the security token to every request. The Monitor keeps the received bytes
in memory (the newest 400 KB) and redraws them in whichever view you choose.

**The Serial Wizard features** (monitor, plot, flashing and Modbus) were
recreated from LCD Wizard’s public SerialWizard documentation and screenshots
of its interface. The author had no access to SerialWizard’s source code, and
none of it is used. See [Where Vundu_lab came from](#where-vundu_lab-came-from).

**Changing the look.** The colours and fonts are variables at the top of `
index.html`: `\--bg` (`\#141414`) is the background and `\--acc` (`\#FFCC14`) is
the highlight.

## Troubleshooting


|Problem                                                          |Fix                                                                                                                                                                                                                                                                         |
|-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|The start-up check lists items as MISSING                        |Follow the `\->` lines under each one. The app still starts, and the Install button in the Monitor and Flash tabs does the serial-tools part for you.                                                                                                                       |
|Flash says “No module named esptool”, or Detect chip does nothing|The flasher is not in `data/engines/serial/venv`. Press **Install (one-off)** in the sidebar (it appears when the tools are missing). Do not create or rename folders by hand.                                                                                              |
|`cd` says “No such file or directory”                            |Your path has a space in it. Put it in quotes: `cd "/home/you/My Projects/Vundu_lab_V0.1.0"`.                                                                                                                                                                               |
|Monitor shows “Not a valid stop bit size” (V0.0.3 only)          |A bug in V0.0.3, fixed in V0.0.4. Update.                                                                                                                                                                                                                                   |
|The board restarts when you press Connect                        |Normal for boards with built-in USB (such as the ESP32-C6): opening the port can reset the chip. It reconnects by itself.                                                                                                                                                   |
|Connected, but the Monitor stays empty                           |Check the baud rate. It must match `Serial.begin(...)` in your code (LCD Wizard exports use 115200). Boards with built-in USB only print on the USB port if the firmware sends `Serial` output to USB (the “USB CDC on boot” build setting); otherwise it goes to the UART pins.|
|Plot shows nothing                                               |The board must print lines ending in a newline, in one of the formats above, at the baud rate you connected with.                                                                                                                                                           |
|Modbus “No reply (timeout)”                                      |Check the unit number, baud rate and parity (RTU), the wiring and A/B polarity, or the host and port (TCP). Try the demo device to confirm Vundu_lab itself is fine.                                                                                                            |
|The port list says “No board detected”                           |Plug the board in (use a USB cable that carries data) and press the refresh button. Only USB serial devices are listed.                                                                                                                                                     |
|Flash and Monitor ask to install serial tools                    |Press **Install (one-off)**. It needs an internet connection and `python3-venv`.                                                                                                                                                                                            |
|“Cannot open the port: busy or access denied”                    |Close the Arduino IDE or PlatformIO monitor and any other serial tool. On Linux also check the `dialout` group (see below).                                                                                                                                                 |
|Linux: no permission for the port                                |`sudo usermod -aG dialout $USER`, then **log out and back in**. The group only applies from your next sign-in.                                                                                                                                                              |
|Flash cannot reach the bootloader                                |Choose **Hold BOOT** under *Enter bootloader*: hold the board’s BOOT button, tap RESET, then press Flash. Also try a shorter USB cable that carries data.                                                                                                                   |
|Garbage characters in the Monitor                                |Wrong baud rate. It must match `Serial.begin(...)` in your code (LCD Wizard exports use 115200).                                                                                                                                                                            |
|The address in the terminal is not 8765                          |Port 8765 was busy, so the next free one was used. Use the address printed in the terminal.                                                                                                                                                                                 |
|`python: command not found`                                      |Use `python3`.                                                                                                                                                                                                                                                              |
|First compile fails with an `ensurepip` or `venv` error          |`sudo apt install python3-venv`                                                                                                                                                                                                                                             |
|Open Folder asks you to paste a path                             |`sudo apt install python3-tk` for the native dialog.                                                                                                                                                                                                                        |
|“Could not build the merged .bin”                                |The compile still worked. Use the separate files, and check the output just above that line for the reason.                                                                                                                                                                 |
|A build seems stuck                                              |Press **Stop**, then Compile again. Downloads resume where they can.                                                                                                                                                                                                        |
|A path with spaces fails in the terminal                         |Put the path in quotes: `cd "Vundu_lab"`                                                                                                                                                                                                                                        |

- - -
## Version history


|Version|What changed                                                                                                                                                                                                                                                                                                                                                                                                           |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**V0.0.9**|The header now says “ESP32 export”. The README has new sections: **Supported boards and chips** (with exactly what has been tested), **What compiles from what** (taken from the code), and **Where Vundu_lab came from** (its relationship to SerialWizard). No code changes apart from the header text and version number.                                                                                               |
|**V0.0.8**|The header now says “LVGL export”, the server file is renamed `vundu_lab.py` (so it cannot be mixed up with another app called Vundu_lab), and the README is back to its V0.0.6 layout. Nothing else changed.                                                                                                                                                                                                              |
|**V0.0.7**|Renamed from Firmware Wizard to **Vundu_lab**: new name, logo and dark theme, now under MindFarter on GitHub with an MIT licence. Everything else unchanged.                                                                                                                                                                                                                                                               |
|**V0.0.6**|Start-up check: the server reports what it depends on and the exact fix for anything missing. Nothing else changed.                                                                                                                                                                                                                                                                                                    |
|**V0.0.5**|One real folder for the serial tools (`data/engines/serial/venv`), a strict “installed” check that ignores a `pyserial` found elsewhere, and automatic repair of a renamed engine folder. The Monitor is switched off while the Flash tab is open and comes back afterwards. Detect chip also reads the flash. Folder dialogs start in a sensible place, and log commands are quoted so they can be pasted into a terminal.|
|**V0.0.4**|Fixed Connect failing with “Not a valid stop bit size”: two elements shared a name. Bad serial settings now fall back to safe defaults.                                                                                                                                                                                                                                                                                |
|**V0.0.3**|Added the Plot and Modbus tabs, including the built-in Modbus demo device.                                                                                                                                                                                                                                                                                                                                             |
|**V0.0.2**|Serial Wizard-style layout with the connection sidebar. Rebuilt Monitor and Flash. **Send to Flash** after a compile. Port list shows only USB boards. Firmware files are recognised from their contents.                                                                                                                                                                                                              |
|**V0.0.1**|First combined release: Compile, Flash and Monitor in one local server. Free-port fallback and a per-run security token. Built on Compiler Wizard V0.4.                                                                                                                                                                                                                                                                |

- - -
## Credits and licences

**Vundu_lab is a convenience wizard. It is not a fork, replacement or rebranding of
any project below, and it does not change their names, behaviour or code.** It
does not include or redistribute any of them. On first use it downloads each
one from its official source onto your own computer and then simply runs it.

All credit for compiling and flashing belongs to the developers and
contributors of:

- **PlatformIO**: the build system and package manager behind the PlatformIO and
  pioarduino engines. <https://platformio.org>
- **pioarduino**: the community-maintained ESP32 platform for PlatformIO, with
  newer Arduino-ESP32 and ESP-IDF releases and newer chips. 
  <https://github.com/pioarduino/platform-espressif32>
- **Arduino**: Arduino CLI and the Arduino IDE, the foundation of the Arduino
  ecosystem and the engine behind the Arduino IDE button. 
  <https://github.com/arduino/arduino-cli>
- **Espressif**: `esptool`, which does the flashing and builds merged images,
  plus the Arduino-ESP32 core and ESP-IDF. 
  <https://github.com/espressif/esptool>
- **pyserial**: the serial port library behind the Monitor. 
  <https://github.com/pyserial/pyserial>

Also at work underneath: the board-support maintainers for RP2040
(Arduino-Pico) and STM32 (STM32duino), and LVGL and the other libraries your
project is built on.

Modbus is an open protocol published by the Modbus Organization. Vundu_lab
implements it from that public specification.

Each of these projects **remains under its own licence**, which applies to
everything Vundu_lab downloads and runs. PlatformIO Core and the pioarduino
platform are Apache 2.0, Arduino CLI is GPL-3.0, `esptool` is
GPL-2.0-or-later and `pyserial` is BSD-3-Clause, but licences change and have
exceptions, so please check each project’s own repository for the current
terms. If you redistribute any of these tools yourself, you are responsible for
following their licences.

**Licence files:**

- **pioarduino:** <https://github.com/pioarduino/platform-espressif32/blob/master/LICENSE>
- **PlatformIO Core:** <https://github.com/platformio/platformio-core/blob/develop/LICENSE.txt>
- **Arduino CLI:** <https://github.com/arduino/arduino-cli/blob/master/LICENSE.txt>
- **esptool:** <https://github.com/espressif/esptool/blob/master/LICENSE>
- **pyserial:** <https://github.com/pyserial/pyserial/blob/master/LICENSE.txt>

Please support the projects that make this possible: star them, report bugs to
them, and sponsor them where you can.

### Not affiliated

Vundu_lab is an independent open-source project by 
[MindFarter](https://github.com/MindFarter). It is not affiliated with,
endorsed by, or supported by PlatformIO, pioarduino, Arduino, Espressif or the
maintainers of any other project named here. Problems with the engines
themselves belong with those projects. “PlatformIO”, “Arduino” and the other
names belong to their owners and are used only to say which tool does what.

**Vundu_lab has no affiliation with LCD Wizard or SerialWizard.** The only thing they
share is that some of Vundu_lab’s features are similar to SerialWizard’s. “LCD
Wizard” and “SerialWizard” are names that belong to their owners, and they are
used here only to say where the ideas came from and which exports Vundu_lab can
compile. Vundu_lab is not an official product of LCD Wizard and is not endorsed by
it.

### Where Vundu_lab came from

Vundu_lab was originally built by a member of the LCD Wizard community, to make
compiling and flashing LCD Wizard exports easier. It is now released under the
MIT licence, for the benefit of everyone who might want to use it.

How it relates to SerialWizard, in detail:

- **A recreation, not a copy.** Vundu_lab’s Monitor, Plot, Flash and Modbus tabs
  recreate the features of LCD Wizard’s SerialWizard (a serial monitor, a
  plotter, an ESP32 flasher and a Modbus master in one window), and their
  layout is deliberately similar. They were written from scratch.
- **Built from public information only.** The author worked from SerialWizard’s
  public documentation and from screenshots of its interface. The author had **no
  access to SerialWizard’s source code**, and **no SerialWizard code is used**.
  The serial, flashing and Modbus parts are built on open-source tools
  (pyserial and esptool) and on the public Modbus specification, as described
  above.
- **What Vundu_lab adds.** The **Compile** tab: an easy compiler built on PlatformIO,
  pioarduino and Arduino CLI, so a project can go from a folder to a flashed
  board in one place. Also **Send to Flash**, the start-up check, and Vundu_lab’s own
  look.

- - -
## Licence (MIT)

MIT License

Copyright (c) 2026 MindFarter (<https://github.com/MindFarter/Vundu_lab>)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This licence covers Vundu_lab’s own code (`vundu_lab.py` and `index.html`) and
documentation. The tools it downloads and runs keep their own licences, as
described above. The same text is in the `LICENSE` file.

