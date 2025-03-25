let
  pconfig = { config = { allowUnfree = true; cudaSupport = true; }; };  
  pkgs =     import <nixpkgs>        pconfig;
  unstable = import <nixos-unstable> pconfig;
in
let
  python =   pkgs.python312;
  pp =       pkgs.python312Packages;
in
  pkgs.mkShell rec {
  name = "desc-ementas";
  pname = name;
  enableParallelBuilding = true;
  
  buildInputs =  (
    with pkgs;(
      [
        chromedriver
        google-chrome
        geckodriver
        jdk
        pdm
        glibc
        zlib
      ]
    ) ++ [ python ] ++ (
      with pp; [
        ipykernel
        nbconvert
        selenium
        pandas
        tabula-py
        tqdm
      ]
    )
  );

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath buildInputs}:$LD_LIBRARY_PATH"
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib.outPath}/lib:$LD_LIBRARY_PATH"

    function code_here() {
      nohup code --disable-gpu ./ >/dev/null 2>&1 && echo;      
    }
    
    function get_git_branch() {
      git name-rev --name-only HEAD > /dev/null 2>&1
      if [[ $? -eq 0 ]]; then
        echo "($(git name-rev --name-only HEAD))";
      else
        echo "";
      fi
    };
    PS1="\n\[\033[1;31m\][${name}:\w]\n\$(get_git_branch)\$\[\033[0m\] ";
  '';
}
