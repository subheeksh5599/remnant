<p align="center">
  <a href="https://github.com/subheeksh5599/remnant"><img src="docs/remnant-banner.png" width="750" alt="REMNANT"></a>
</p>

<p align="center">
    <em>The Minds agent that remembers what communities leave behind.</em>
</p>

<p align="center">
<a href="https://remnant-two.vercel.app" target="_blank">
    <img src="https://img.shields.io/website/https/remnant-two.vercel.app" alt="Website">
</a>
<a href="https://github.com/subheeksh5599/remnant/actions/workflows/test.yml" target="_blank">
    <img src="https://github.com/subheeksh5599/remnant/actions/workflows/test.yml/badge.svg" alt="Test">
</a>
<a href="https://opensource.org/licenses/MIT" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>
</p>

---

**Website**: <a href="https://remnant-two.vercel.app/" target="_blank">remnant-two.vercel.app</a>

**Documentation**: <a href="https://github.com/subheeksh5599/remnant/tree/main/docs" target="_blank">docs</a>

**REMNANT Mind**: <a href="https://github.com/subheeksh5599/remnant" target="_blank">Repository</a>

---

REMNANT is the persistent community-memory agent allowing you to effortlessly discover recurring audience needs that amplify creator-audience engagement across all aspects of community growth.

**[Features](#features)** - **[Requirements](#requirements)** - **[Installation](#installation)** - **[Usage](#usage)** - **[Plugins](#plugins)** - **[Contributing](#contributing)**

## Features

- Easy to use, persistent agent framework to discover community needs fast.
- Cross-language need discovery powered by a transparent concept glossary.
- Competing explanations (H1–H4) with evidence for and against each hypothesis.
- Pre-registered experiments with deterministic, auditable verdicts.
- Minds memory mirroring with recovery — the agent's narrative survives restarts.

## Requirements

**REMNANT requires Python version 3.12 or higher.**

> It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) for installing remnant, in order to avoid dependency conflicts. You can use your favorite virtual environment management system, like [conda](https://docs.conda.io/en/latest/), [poetry](https://python-poetry.org/), or [uv](https://docs.astral.sh/uv/) for example.

Furthermore, the following software packages need to be installed in your system:

- **Ubuntu**: `sudo apt-get install python3.12 python3.12-venv curl git`
- **Mac OS**: `brew install python@3.12 git curl`
- **Windows**

    > Windows support is currently under development. For the time being, we highly recommend using [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and then following the Linux instructions. If you still want to try to get REMNANT to work natively on Windows, you will need to install the following software packages: [Python 3.12](https://www.python.org/downloads/), [git](https://git-scm.com/download/win), and [curl](https://curl.se/windows/)

## Installation

You can install REMNANT directly from the repository:

```bash
git clone https://github.com/subheeksh5599/remnant.git
cd remnant/backend
uv venv .venv
uv pip install -e .
```

Then you can run remnant in your python shell, notebook or application as follows:

```python
from remnant.app import app
```

... and just like that, you're ready to go! Now, there are multiple ways to configure REMNANT, refer to the [relevant documentation pages](https://github.com/subheeksh5599/remnant/tree/main/docs) for more information.

## Usage

For example, [ingest the labeled demo corpus](https://github.com/subheeksh5599/remnant/blob/main/backend/remnant/scripts_loader.py) and let discovery surface the needs.

And then run it using remnant:

```python
from fastapi.testclient import TestClient
from remnant.app import app

with TestClient(app) as c:
    c.post("/api/v1/demo/load")          # labeled synthetic corpus, discovered not pre-encoded
    remnants = c.get("/api/v1/remnants").json()
    print([r["title"] for r in remnants])
```

Please refer to the [documentation](https://github.com/subheeksh5599/remnant/tree/main/docs) to learn more about how to use remnant.

## Plugins

REMNANT thrives on its rich [data source](https://github.com/subheeksh5599/remnant/tree/main/docs) ecosystem. There are ingestion paths for many different community surfaces and the list is growing:

- YouTube comments
- GitHub discussions and issues
- Discord / Telegram exports
- Twitter mentions
- Email digests
- Kaggle / dataset imports

If you want to develop your own importer for remnant, consult the [plugin development documentation](https://github.com/subheeksh5599/remnant/blob/main/backend/remnant/ingest.py), you'll be surprised how simple it is.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/subheeksh5599"><img src="https://avatars.githubusercontent.com/u/251461028?v=4" width="100px;" alt="Komari Subheeksh"/><br /><sub><b>Komari Subheeksh</b></sub></td>
    </tr>
  </tbody>
</table>
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

Want to be part of the persistent community-memory revolution? All contributions are welcome! Check out our [contribution guide](https://github.com/subheeksh5599/remnant/tree/main/docs) to learn more about how to develop with and for remnant.