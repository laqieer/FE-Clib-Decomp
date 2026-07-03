# FE-Clib-Decomp
C library generated from decomp projects for Fire Emblem modding

## Powered by

The checked-in `.lds`, `lyn` reference `.s`, and Event Assembler `.event` outputs are generated from these decompilation ELFs:

- [FE6: The Binding Blade](https://github.com/FireEmblemUniverse/fireemblem6j) - supplies FE6 symbols from `fireemblem6j/fe6.elf`.
- [FE8U: The Sacred Stones](https://github.com/laqieer/fireemblem8u) - supplies FE8U symbols from `fireemblem8u/fireemblem8.elf`.
- [FE8J: 聖魔の光石 / Seima no Kouseki](https://github.com/laqieer/fireemblem8j) - supplies FE8J symbols from `fireemblem8j/fireemblem8.elf`.

## User Guide

`INCLUDE output/xxx.lds` in linker script

To generate a lyn/FE-CLib reference assembly file and an Event Assembler include from a
decomp ELF:

```sh
python3 utility/make_lyn_reference.py \
  ../fireemblem8u/fireemblem8.elf \
  --lyn-reference output/fe8u-reference.s \
  --ea-defines output/fe8u-defines.event \
  --snapshot "laqieer/fireemblem8u master"
```

Assemble the reference and use it with `lyn`:

```sh
arm-none-eabi-as output/fe8u-reference.s -o output/fe8u-reference.o
lyn hack.o output/fe8u-reference.o > hack.lyn.event
```

Use the generated Event Assembler definitions directly from `.event` scripts:

```event
#include "fe8u-defines.event"
```

Generated outputs currently checked in:

- `output/fe8u.lds`
- `output/fe8u-reference.s`
- `output/fe8u-defines.event`
- `output/fe8j.lds`
- `output/fe8j-reference.s`
- `output/fe8j-defines.event`
- `output/fe6.lds`
- `output/fe6-reference.s`
- `output/fe6-defines.event`

## Developer Guide

```
pip install -r utility/requirements.txt
python3 utility/make_linker_script.py -h
python3 utility/make_lyn_reference.py -h
```
