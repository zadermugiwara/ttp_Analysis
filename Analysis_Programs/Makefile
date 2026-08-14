CXX ?= g++
ROOT_CONFIG ?= root-config
FASTJET_CONFIG ?= fastjet-config
HEPMC_PREFIX ?= /usr/local

ROOT_CFLAGS := $(shell $(ROOT_CONFIG) --cflags)
ROOT_LIBS := $(shell $(ROOT_CONFIG) --glibs)
FASTJET_CFLAGS := $(shell $(FASTJET_CONFIG) --cxxflags)
FASTJET_LIBS := $(shell $(FASTJET_CONFIG) --libs)

CPPFLAGS += -I$(HEPMC_PREFIX)/include $(FASTJET_CFLAGS) $(ROOT_CFLAGS)
CXXFLAGS ?= -O2
CXXFLAGS += -std=c++17 -Wall -Wextra -Wno-deprecated
LDFLAGS += -L$(HEPMC_PREFIX)/lib
LDLIBS += -lHepMC $(FASTJET_LIBS) -lfastjettools -lValenciaPlugin $(ROOT_LIBS)

.PHONY: all clean

all: ttp_Analysis

ttp_Analysis: ttp_Analysis.o
	$(CXX) $(LDFLAGS) $^ $(LDLIBS) -o $@

ttp_Analysis.o: ttp_Analysis.cc $(wildcard Headers_Analysis/*.hh)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f ttp_Analysis ttp_Analysis.o
