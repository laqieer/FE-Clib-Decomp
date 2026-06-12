# FE-Clib-Decomp
C library generated from decomp projects for Fire Emblem modding

## User Guide

`INCLUDE output/xxx.lds` in linker script

To generate a lyn/FE-CLib reference assembly file and an Event Assembler include from a
decomp ELF:

```sh
python3 utility/make_lyn_reference.py \
  ../fireemblem8u/fireemblem8.elf \
  --lyn-reference output/fe8u-decomp-reference.s \
  --ea-defines output/fe8u-decomp-defines.event \
  --snapshot "laqieer/fireemblem8u master"
```

Assemble the reference and use it with `lyn`:

```sh
arm-none-eabi-as output/fe8u-decomp-reference.s -o output/fe8u-decomp-reference.o
lyn hack.o output/fe8u-decomp-reference.o > hack.lyn.event
```

Use the generated Event Assembler definitions directly from `.event` scripts:

```event
#include "fe8u-decomp-defines.event"
```

## Developer Guide

```
pip install -r utility/requirements.txt
python3 utility/make_linker_script.py -h
python3 utility/make_lyn_reference.py -h
```
