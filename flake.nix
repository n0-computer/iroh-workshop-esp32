{
  description = "Development environment for the iroh ESP32 workshop";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, rust-overlay, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ (import rust-overlay) ];
          };

          nightlyRust = pkgs.rust-bin.nightly."2026-09-03".default.override {
            extensions = [ "rust-src" "rustfmt" "clippy" ];
          };
          stableRust = pkgs.rust-bin.stable.latest.default.override {
            extensions = [ "rustfmt" "clippy" ];
            targets = [ "wasm32-unknown-unknown" ];
          };

          commonPackages = with pkgs; [
            gcc
            clang
            wasm-bindgen-cli_0_2_126
            gnumake
            cmake
            ninja
            pkg-config
            python3
            git
            espflash
            ldproxy
            llvmPackages.libclang
          ];

          linuxPackages = with pkgs; lib.optionals stdenv.hostPlatform.isLinux [
            libudev-zero
            libusb1
          ];

          mkShell = rust: pkgs.mkShell {
            packages = commonPackages ++ linuxPackages ++ [ rust ];
            WIFI_CONFIG = "Zamfiresku:airplane";

            # Make the Nix-provided libudev visible to espflash at runtime.
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath linuxPackages;

            # Let bindgen/clang-sys find the Nix-provided shared libclang.
            LIBCLANG_PATH = "${pkgs.llvmPackages.libclang.lib}/lib";
          };
        in {
          default = mkShell nightlyRust;
          stable = mkShell stableRust;
        }
      );
    };
}
