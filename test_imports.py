#!/usr/bin/env python3

import sys

try:
    import main
    print("✓ main.py imports successfully")
except Exception as e:
    print(f"✗ main.py import failed: {e}")
    sys.exit(1)

try:
    import config
    print("✓ config.py imports successfully")
except Exception as e:
    print(f"✗ config.py import failed: {e}")
    sys.exit(1)

cogs_to_test = [
    'cogs.antinuke',
    'cogs.logging',
    'cogs.moderation',
    'cogs.roles',
    'cogs.roleplay',
    'cogs.settings',
    'cogs.voicechannel',
    'cogs.leveling',
    'cogs.economy',
    'cogs.warns',
    'cogs.boosters'
]

for cog in cogs_to_test:
    try:
        __import__(cog)
        print(f"✓ {cog} imports successfully")
    except Exception as e:
        print(f"✗ {cog} import failed: {e}")
        sys.exit(1)

utils_to_test = [
    'utils.checks',
    'utils.config_manager',
    'utils.formatting',
    'utils.vc_manager'
]

for util in utils_to_test:
    try:
        __import__(util)
        print(f"✓ {util} imports successfully")
    except Exception as e:
        print(f"✗ {util} import failed: {e}")
        sys.exit(1)

print("\n✅ All imports successful! Bot code is ready to run.")
print("📝 Note: Create .env file with DISCORD_TOKEN and OWNER_ID before running the bot.")
