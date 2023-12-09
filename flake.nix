{
  description = ''
    A web scraper for chess coaches. 

    To generate a copy of this template elsewhere, refer to:
    https://github.com/jrpotter/bootstrap
  '';

  inputs = {
    flake-compat.url = "https://flakehub.com/f/edolstra/flake-compat/1.tar.gz";
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # See https://github.com/nix-community/poetry2nix/tree/master#api for
        # more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};

        inherit
          (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
          mkPoetryApplication
          defaultPoetryOverrides;

        # https://github.com/nix-community/poetry2nix/blob/ec4364021900f8e0d425d901b6e6ff03cf201efb/docs/edgecases.md
        # `poetry2nix`, by default, prefers building from source. To build
        # certain dependencies, we need to augment its build dependencies by
        # adding the corresponding build backend (e.g. `setuptools`).
        #
        # For example, you can write:
        # ```nix
        # pypkgs-build-requirements = {
        #   ...
        #   coolname = [ "setuptools" ];
        #   ...
        # };
        # ```
        # after encountering a build error like:
        #
        # > ModuleNotFoundError: No module named 'setuptools'
        pypkgs-build-requirements = {};
        poetry2nix-overrides = defaultPoetryOverrides.extend (self: super:
          builtins.mapAttrs (package: build-requirements:
            (builtins.getAttr package super).overridePythonAttrs (old: {
              buildInputs =
                (old.buildInputs or []) ++
                (builtins.map (pkg:
                  if builtins.isString pkg then
                    builtins.getAttr pkg super
                  else
                    pkg) build-requirements);
            })
          ) pypkgs-build-requirements
        );

        types = with pkgs.python311Packages; {
          beautifulsoup4 = buildPythonPackage rec {
            pname = "types-beautifulsoup4";
            version = "4.12.0.7";
            src = pkgs.fetchPypi {
              inherit pname version;
              sha256 = "sha256-WZgAKNKb9V0Ns1nvowW3W6zwy5Lj8/az/UCPJTHfJ0w";
            };
            doCheck = false;
          };
          psycopg2 = buildPythonPackage rec {
            pname = "types-psycopg2";
            version = "2.9.21.19";
            src = pkgs.fetchPypi {
              inherit pname version;
              sha256 = "sha256-7DquUi3enEEUFZe8QRI7TJVftAk7H8fsbuYHeVoKCI8=";
            };
            doCheck = false;
          };
        };
      in
      {
        packages = {
          app = mkPoetryApplication {
            projectDir = ./.;
            overrides = poetry2nix-overrides;
            preferWheels = true;
          } // {
            # These attributes are passed to `buildPythonApplication`.
            pname = "coach-scraper";
            version = "0.1.3";
          };

          default = self.packages.${system}.app;
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            poetry
            postgresql_15
          ] ++ (with pkgs.python311Packages; [
            black
            debugpy
            mccabe
            mypy
            pycodestyle
            pyflakes
            pyls-isort
            python-lsp-black
            python-lsp-server
            types.beautifulsoup4
            types.psycopg2
            typing-extensions
          ]);
        };
      });
}
