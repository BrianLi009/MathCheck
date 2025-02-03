MROOT := $(shell pwd)
export MROOT

# Add nauty library path and linking
NAUTY_DIR = ../nauty2_8_8
NAUTY_LIB = $(NAUTY_DIR)/nauty.a

# Add to CFLAGS and LFLAGS
CFLAGS += -I$(NAUTY_DIR)
LFLAGS += $(NAUTY_LIB)

minisat:
	make -C simp rs

debug:
	make -C simp d

clean:
	make -C simp clean
