import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def names_in_settings():
    text = (ROOT / "suffolkcoins" / "settings.py").read_text()
    return set(re.findall(r'env(?:_bool|_list)?\(\s*"([A-Z_]+)"', text))


def names_in_example():
    found = set()
    for line in (ROOT / ".env.example").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            found.add(line.split("=", 1)[0].strip())
    return found


def test_every_setting_read_from_the_environment_is_documented():
    missing = names_in_settings() - names_in_example()
    assert missing == set(), f"add to .env.example: {sorted(missing)}"


def test_the_example_names_no_unknown_variable():
    unknown = names_in_example() - names_in_settings()
    assert unknown == set(), f"not read by settings.py (typo?): {sorted(unknown)}"
