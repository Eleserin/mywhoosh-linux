# Tests for `patch_windows_connectivity_dll.py`

Run from the repo root:

```sh
python3 -m unittest discover -s patch/tests
```

No third-party dependencies (stdlib `unittest`).

## Fixtures

`fixtures/` holds the real `WindowsConnectivity.dll` from two MyWhoosh releases:

| File                            | MyWhoosh | `IsBluetoothEnabled` body offset |
|---------------------------------|----------|----------------------------------|
| `WindowsConnectivity_5.7.2.dll` | 5.7.2    | `0xc50`                          |
| `WindowsConnectivity_5.8.2.dll` | 5.8.2    | `0xc70`                          |

The differing offsets are the reason the patcher resolves the method by name
instead of a hardcoded offset; the tests assert the patch lands correctly on
both.
