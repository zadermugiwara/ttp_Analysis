# C++ flags
CXX         = g++

# Set library flags for compiler
LDFLAGS     = -Wl,-undefined,dynamic_lookup

# HepMC
HepMCdir    = /home/higinio/Documentos/ASE/HERWIG
HepMClib    = -L$(HepMCdir)/install/lib -lHepMC

# FastJet
FastJetdir  = /home/higinio/Documentos/ASE/HERWIG
FastJetlib  = -L$(FastJetdir)/lib -lfastjet -lfastjettools -lValenciaPlugin

# ROOTSYS defined in .bashrc as environment variable
ROOTCFLAGS  := $(shell $(ROOTSYS)/bin/root-config --cflags)
ROOTGLIBS   := $(shell $(ROOTSYS)/bin/root-config --glibs)

# Includes
INCLUDES    = -I$(HepMCdir)/include -I$(FastJetdir)/include -I$(ROOTSYS)/include -I./include 
#INCLUDES    = -I$(HepMCdir)/include -I$(FastJetdir)/include -I/home/higinio/Documentos/ASE/Analysis/root/root/include -I./include 

# Flags for compiler
CXXFLAGS    =  -ansi -Wpedantic -Wall -O2 -Wno-long-long $(ROOTCFLAGS) $(INCLUDES)

#export DYLD_LIBRARY_PATH = /Users/oscar/Documents/HEP/HepMC/hepmc-install/lib

# ----------------------------------------------------------------------------
# Rules

.SUFFIXES:  .o .cxx .f .exe

###############################################################################
# Instructions for building a .o file from a .cxx file
#
.cc.o:  $(HDRS) $<
	@echo "Compiling $< with $(CXX) ..."
	@$(CXX) $(CXXFLAGS) -c -Wno-deprecated $< -o $@


ttp_Analysis: ttp_Analysis.o
	@echo "Building $@	 ..."
	$(CXX) $(CXXFLAGS) ttp_Analysis.o \
		$(HepMClib) \
		$(FastJetlib) \
		$(ROOTGLIBS)  -o $@

clean:
	rm ttp_Analysis
	rm *.o
