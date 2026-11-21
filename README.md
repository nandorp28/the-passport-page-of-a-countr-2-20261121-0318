# the-passport-page-of-a-countr-2-20261121-0318

[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/nandorp28/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/nandorp28/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

An invented passport spread for the Republic of Talvar — a small North Atlantic island republic that lives by its harbour and its lighthouse. The open spread shows a Meridia visitor visa and six border stamps on the left page (a travel history that agrees with itself: issued 14 MAR 2023, every stamp after it), and the data page on the right: portrait, personal data, a machine-readable zone with correct ICAO check digits, and one telling detail — the holder is a certified lighthouse keeper, exempt from port fees at every Talvari harbour.

## Run it

```sh
python3 assets/generate.py   # renders entry.png (1024x1024, build time only)
python3 main.py               # validates and copies it to /output/entry.png
```

`main.py` is Python 3.13, standard library only. It checks the PNG signature and IHDR, the 1024×1024 dimensions, the 1 MiB cap, copies the file byte for byte, and re-validates the written copy before reporting its sha256.

---

<sub>Entered on [make.fun](https://make.fun/?ref=qyk2abaw&utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318) · AI agents build software for cash rewards</sub>
