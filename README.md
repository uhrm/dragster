# dragster
Dragster Analysis and Simulation

## Setting up Stella

    git submodule init stella
    git submodule update stella
    cd stella
    CXXFLAGS="-g -O0" ./configure --enable-debugger
    make -j 8

## Running the demo script

    mkdir -p data
    ./stella/stella -logtoconsole 1 -threads 0 -video software -sound 0 -timing busy -snapsavedir ./data -debug <path/to/ROM>

In Stella's debugger prompt run:

    exec scripts/demo

## Creating an interactive SVG info-graphic

    python3.6 plot.py demo

This should create an SVG file in folder `docs/plots/`.
