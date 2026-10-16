# iroh on ESP32: workshop

Peer-to-peer networking with [iroh] on ESP32 microcontrollers, in small steps.
Each step is a directory with its own program; you can jump to any of them.

## Hardware

<img src="images/xiao-esp32-c5.png" alt="Seeed Studio XIAO ESP32-C5" width="200">

The board is the [Seeed Studio XIAO ESP32-C5], a thumbnail-sized (21 × 17.8 mm)
board around Espressif's ESP32-C5 chip:

| | |
|---|---|
| CPU | 32-bit RISC-V, single core, 240 MHz |
| RAM | 384 KB on-chip SRAM, plus 8 MB PSRAM. iroh's heap lives in the PSRAM. |
| Flash | 8 MB |
| Radio | dual-band WiFi 6 (2.4 and 5 GHz), Bluetooth LE 5 |
| USB | USB-C, for power, flashing and the serial log |
| On board | a yellow user LED on GPIO27 (lit when the pin is low), a BOOT button on GPIO28 (reads low while pressed), a reset button |

Steps 1 to 4 need nothing but the board. The LED is the light in steps 3 and
4, and BOOT is the button in step 4. Step 5 adds a photoresistor, a push button
and a lamp; the wiring is in [`05-lamp/src/main.rs`](05-lamp/src/main.rs).

Two things that trip people up:

- **Plug in the antenna.** The board comes with an external antenna on a tiny
  U.FL connector. Without it, WiFi barely works.
- **Use a USB-C cable that carries data.** A charge-only cable powers the board,
  but `espflash` won't find it.

For the full pinout, see Seeed's [getting started page].

## Before the workshop

The first build downloads and compiles ESP-IDF, Espressif's SDK: several GB and
a good while.

1. Install the system packages: a C compiler and linker (rustup doesn't bring
   one), Python 3.9 or newer for the ESP-IDF build, and `libudev` for `espflash`.

   ```sh
   # Debian/Ubuntu: python3-venv is a separate package there, and the ESP-IDF
   # build fails halfway without it.
   sudo apt install build-essential pkg-config libudev-dev python3 python3-venv
   # Fedora
   sudo dnf install gcc pkgconf-pkg-config systemd-devel python3
   # Arch
   sudo pacman -S --needed base-devel python
   # macOS: the command line tools bring the compiler.
   xcode-select --install
   ```

   On Linux, to use the board's serial port, add yourself to the `dialout`
   group (`uucp` on Arch), then log out and back in:
   `sudo usermod -aG dialout $USER`.
2. Install [Rust](https://rustup.rs). The right nightly installs itself the
   first time you build here (see `rust-toolchain.toml`). No `espup` needed: the
   C5 is RISC-V.
3. Install the flashing and linking tools:

   ```sh
   cargo install espflash ldproxy
   ```
4. Build the first step once:

   ```sh
   cd 01-hello
   WIFI_CONFIG='your-ssid:your-password' cargo build --release
   ```

   For an open network, just `WIFI_CONFIG='your-ssid'`. If that finishes,
   you're set. (The other steps share that build.)
5. For the web pages: `rustup target add wasm32-unknown-unknown` and
   `cargo install wasm-bindgen-cli --version 0.2.126`.

## The web pages

Each step has a page that talks to the device: iroh compiled to WebAssembly,
running in the browser and reaching the device over a relay (browsers can't send
UDP). Build and serve them once:

```sh
cd web
npm run build
npm run serve   # http://localhost:8080
```

Use Chrome, Firefox or Safari; any of them works for these pages.

## Steps

Run a step from its directory; `cargo run` flashes the board over USB and opens
the serial monitor:

```sh
cd 01-hello
WIFI_CONFIG='your-ssid:your-password' cargo run --release
```

Each step's `main.rs` is short; the boilerplate (WiFi, an iroh endpoint sized
for a microcontroller) is in [`esp32/`](esp32/src/lib.rs). Compare a step
with the previous one (`diff 02-identity/src/main.rs 03-light/src/main.rs`) to
see what's new.

### 01-hello: an endpoint

Join WiFi, start an iroh endpoint, and print its endpoint id: the public key
anyone can dial it with.

```text
I (…) hello: Hello from iroh! My endpoint id is 5a1f…
```

There's no stored key yet, so every start prints a different id. Paste it into
**page 1**: the device answers, but turns the connection away, since it doesn't
offer any protocol yet.

### 02-identity: a stable endpoint id

The secret key is generated once and kept in flash (NVS), so the endpoint id
survives restarts and reflashing. Paste it into **page 2** once: the page
remembers it, and so do the pages after it.

### 03-light: a protocol

The device offers a protocol: switch the LED, ask whether it's on. The protocol
is an enum in [`protocol/src/v1.rs`](protocol/src/v1.rs), shared by the device and
the page, so both speak the same Rust types; [irpc] takes care of the wire
format. Each protocol has an ALPN, a name both sides agree on when connecting.

On **page 3**, switch the light.

### 04-button: watching

The BOOT button toggles the light too, so its state can change without anyone
asking. Protocol version 2 ([`protocol/src/v2.rs`](protocol/src/v2.rs), with its
own ALPN) adds `Watch`: the device sends the current state, then every change.
On **page 4**, press the button and watch the light follow.

### 05-lamp: the whole thing (demo)

Not one to build at the workshop: this is where the steps lead. A lamp you
could put on a shelf, with:

- **WiFi provisioning over Bluetooth** instead of `WIFI_CONFIG`. On first boot the device
  advertises as `lamp-<short endpoint id>`; **page 5** sends it a network,
  sealed with HPKE to its endpoint id so only that device can read it, and
  gets back a pairing ticket (which holds the endpoint id, so it can connect
  right away). Hold BOOT for 5 seconds to forget the network and start over;
  the endpoint id stays. The provisioning code is [iroh-provision].
- **A push button**: press to switch the light, hold for a second to switch
  automatic mode.
- **A photoresistor**: in automatic mode the lamp switches on when it gets
  darker than a threshold (set on page 5; kept across restarts), with a
  margin and a 2-second delay so a passing shadow doesn't switch it.

Protocol version 3 ([`protocol/src/v3.rs`](protocol/src/v3.rs)) answers
everything with the whole state: on/off, mode, brightness and threshold.

The user LED blinks slowly while waiting for WiFi credentials, fast while
joining, and is off once joined.

| XIAO pin | GPIO | Connect to |
|---|---|---|
| D1 | 0 | photoresistor (D1 is its 3.3 V supply) |
| D0 | 1 | photoresistor's other leg (ADC, internal pull-down) |
| D9 | 9 | push button to GND (internal pull-up) |
| D10 | 10 | LED with a resistor to GND, or a logic-level MOSFET for a bigger lamp |

Point the photoresistor away from the lamp: if it sees the lamp, automatic
mode switches it off again. No `WIFI_CONFIG` needed:

```sh
cd 05-lamp
cargo run --release
```

Page 5 needs Chrome or Edge for Web Bluetooth.

Step 5 builds on its own, outside the steps' workspace: it needs Bluetooth,
and with Bluetooth compiled in, the other steps lose their direct connections.
So its first build compiles ESP-IDF again, with its own
[`sdkconfig.defaults`](05-lamp/sdkconfig.defaults) on top of the shared one.

## Layout

Steps 1 to 4 are one Cargo workspace, so ESP-IDF is built once for all of
them. Step 5 has its own build, see above.

| Path | What |
|---|---|
| `esp32/` | WiFi, time, the stored key, and the `esp32::N0` endpoint preset |
| `protocol/` | the light protocols, version 1 (step 3), 2 (step 4) and 3 (step 5) |
| `01-hello/` … `04-button/` | the steps |
| `05-lamp/` | the demo, with its own build and Bluetooth settings |
| `web/` | the pages, one per step (not part of the workspace: it builds for the browser) |
| `slides/` | the intro talk, see [`slides/README.md`](slides/README.md) |
| `quic-talk/` | the "Why iroh uses QUIC" talk, see [`quic-talk/README.md`](quic-talk/README.md) |
| `sdkconfig.defaults` | ESP-IDF settings for all steps (PSRAM, buffer sizes, ...) |
| `05-lamp/sdkconfig.defaults` | Bluetooth, on top of those, for step 5 only |
| `.cargo/config.toml` | target, chip (`MCU`), and the flash command |

## Troubleshooting

- **No serial port / `espflash` can't connect:** use a USB cable that carries
  data, not just power.
- **The board loops through resets and prints nothing useful:** unplug it and
  plug it back in.
- **`waiting for download` after flashing:** the chip was reset back into the
  bootloader. The runner in `.cargo/config.toml` avoids this by resetting once
  after flashing and not again from the monitor; if you changed it, change it
  back. Pressing RESET also works, but it drops the USB connection, so start
  `espflash monitor` again afterwards.
- **`WIFI_CONFIG is not set`:** it's read when building, so it goes on the
  `cargo run` command line.

## License

Copyright 2026 N0, INC.

This project is licensed under either of

 * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or
   https://www.apache.org/licenses/LICENSE-2.0)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or
   https://opensource.org/licenses/MIT)

at your option.

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this project by you, as defined in the Apache-2.0 license,
shall be dual licensed as above, without any additional terms or conditions.

[iroh]: https://www.iroh.computer
[irpc]: https://docs.rs/irpc
[Seeed Studio XIAO ESP32-C5]: https://www.seeedstudio.com/Seeed-Studio-XIAO-ESP32C5-p-6609.html
[getting started page]: https://wiki.seeedstudio.com/xiao_esp32c5_getting_started/
[iroh-provision]: https://github.com/n0-computer/iroh-esp32-examples/tree/main/provisioning
