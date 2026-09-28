cmake_minimum_required(VERSION 3.10)
project(AxiomCore VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

if(MSVC)
    add_compile_options(/O2 /Oi /Ot /GL /arch:AVX2)
else()
    add_compile_options(-O3 -march=native -ffast-math -Wall)
endif()

# Executable target for benchmark suite
add_executable(axiom_benchmark benchmarks/benchmark.cpp)
if(WIN32)
    target_link_libraries(axiom_benchmark ws2_32)
endif()

# Executable target for CLI daemon and query tool
add_executable(axiom_cli src/cli.cpp)
if(WIN32)
    target_link_libraries(axiom_cli ws2_32 shell32 user32)
endif()
