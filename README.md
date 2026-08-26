<p align="center">
  <a href="https://github.com/subheeksh5599/remnant"><img src="docs/remnant-banner.png" width="750" alt="REMNANT"></a>
</p>

<p align="center">
    <em>The Mind that remembers what communities leave behind.</em>
</p>

<p align="center">
<a href="https://remnant-two.vercel.app" target="_blank">
    <img src="https://img.shields.io/website/https/remnant-two.vercel.app" alt="Website">
</a>
<a href="https://github.com/subheeksh5599/remnant/tree/main/backend/tests" target="_blank">
    <img src="https://img.shields.io/badge/tests-61%20passing-3E7A5C" alt="Test">
</a>
<a href="https://www.animocabrands.com/minds" target="_blank">
    <img src="https://img.shields.io/badge/Creative%20Minds%20Jam%20%231-Track%201-5C6B7A" alt="Track">
</a>
<a href="https://opensource.org/licenses/MIT" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>
</p>

---

**Website**: <a href="https://remnant-two.vercel.app/" target="_blank">remnant-two.vercel.app</a>

**Documentation**: <a href="https://github.com/subheeksh5599/remnant/tree/main/docs" target="_blank">docs</a>

**REMNANT Minds**: <a href="https://www.animocabrands.com/minds" target="_blank">Minds by Animoca Brands</a>

---

REMNANT is a persistent Minds agent that discovers candidate recurring needs across a creator's community, preserves competing explanations about why they recur, and learns from pre-registered experiments what is actually worth acting on now.

**[Features](#features)** - **[Requirements](#requirements)** - **[Installation](#installation)** - **[Usage](#usage)** - **[Data sources](#data-sources)** - **[Contributing](#contributing)**

## Features

- Easy to use, persistent mindset for building community-memory intelligence fast.
- Cross-language need discovery via a transparent concept glossary — auditable, no LLM inside the math.
- Competing explanations (H1–H4) with evidence for and against each; contradicting evidence is never suppressed.
- Pre-registered experiments with deterministic verdicts — `observed 0.067 >= threshold 0.040 → CLEARED`.
- Minds memory mirroring with recovery — a fresh session can recover what the agent knew.

## Requirements

**REMNANT requires Python version 3.12 or higher (backend) and Node 18 or higher (frontend).**

> It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) for installing remnant, in order to avoid dependency conflicts. You can use your favorite virtual environment management system, like [conda](https://docs.conda.io/en/latest/), [poetry](https://python-poetry.org/), or [uv](https://docs.astral.sh/uv/) for example.

Furthermore, the following software packages need to be installed in your system:

- **Ubuntu**: `sudo apt-get install python3.12 python3.12-venv curl git nodejs npm`
- **Mac OS**: `brew install python node curl git`
- **Windows**

    > Windows support is currently under development. For the time being, we highly recommend using [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and then following the linux instructions.

## Installation

You can install REMNANT directly from the repository:

```bash
git clone https://github.com/subheeksh5599/remnant.git && cd remnant/backend
uv venv .venv
uv pip install -e .
source .venv/bin/activate
```

Then you can run remnant in your python shell, notebook or application as follows:

```python
from remnant.app import app
```

... and just like that, you're ready to go! Now, there are multiple ways to configure REMNANT, refer to the [relevant documentation pages](https://github.com/subheeksh5599/remnant/tree/main/docs) for more information.

## Usage

For example, [load the demo corpus](https://github.com/subheeksh5599/remnant/tree/main/docs) and let REMNANT discover the needs:

```python
from fastapi.testclient import TestClient
from remnant.app import app

with TestClient(app) as c:
    c.post("/api/v1/demo/load")          # labeled synthetic corpus, discovered not pre-encoded
    r = c.post("/api/v1/remnants", json={
        "title": "Beginner ZK education",
        "underlying_need_hypothesis": "Beginners want an accessible on-ramp to zero-knowledge education.",
    }).json()
    rid = r["remnant_id"]
    c.post(f"/api/v1/remnants/{rid}/expressions", json={
        "text": "Can you make a beginner ZK tutorial?",
        "source_kind": "youtube_comment", "source_id": "yt-2022-01",
        "occurred_at": "2022-06-01T00:00:00Z",
    })
    exp = c.post(f"/api/v1/remnants/{rid}/experiments").json()
    c.post(f"/api/v1/remnants/{rid}/experiments/{exp['experiment_id']}/outcome",
           json={"observed_value": 0.067})   # -> CLEARED, state -> revisited
```

Please refer to the [documentation](https://github.com/subheeksh5599/remnant/tree/main/docs) to learn more about how to use remnant.

## Data sources

REMNANT thrives on its rich community [evidence](https://github.com/subheeksh5599/remnant/tree/main/docs) ecosystem. There are ingestion paths for many different community surfaces and the list is growing:

- YouTube comments
- Discord / Telegram
- GitHub discussions and issues
- Twitter mentions
- Email digests
- Creator-provided exports

If you want to develop a new ingestion path for remnant, consult the [ingestion documentation](https://github.com/subheeksh5599/remnant/tree/main/docs), you'll be surprised how simple it is.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/subheeksh5599"><img src="https://avatars.githubusercontent.com/u/251461028?v=4" width="100px;" alt="Komari Subheeksh"/><br /><sub><b>Komari Subheeksh</b></sub></a></td>
    </tr>
  </tbody>
</table>
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

Want to be part of the persistent community-memory revolution? All contributions are welcome! Check out our [contribution guide](https://github.com/subheeksh5599/remnant/tree/main/docs) to learn more about how to develop with and for remnant.