# LevelApp – AI Evaluation Framework for Continuous Testing

**LevelApp** is a modular, open-source evaluation framework for AI-powered applications. It provides the structure, tooling, and integrations to **evaluate AI systems with multi-turn test scenarios**, **compare expected vs. actual results**, and **prevent regressions in production**.

Whether you're testing an AI assistant, RAG pipeline, or metadata extractor, LevelApp enables **scenario-driven, model-graded evaluations**, with native support for **GitHub CI/CD**.

---

## 🔍 Why LevelApp?

Building AI is hard. Releasing it with confidence is harder.

LevelApp is here to help teams:

- ✅ Validate AI model upgrades before release.
- ✅ Prevent silent regressions in conversations, intents, or outputs.
- ✅ Automate testing using real-world use cases.
- ✅ Get detailed insights on metadata extraction, classification, response quality, and more.

> Think of LevelApp as your **unit test + benchmark** layer for AI products.

---

## 💡 Key Concepts

- **Scenario Presets**: Structured test cases simulating multi-turn user conversations.
- **Metadata Expectations**: Evaluate key data points your AI is supposed to extract (e.g., intents, locations, amounts).
- **Guardrails**: Mark scenarios that require specific handling (e.g., conversation stops, fallback).
- **Batch Evaluation**: Run full evaluations against real or mocked APIs.
- **Model-based Grading**: Use LLMs (e.g. OpenAI, Claude, IONOS) to assess response quality and metadata match.
- **CI/CD Integration**: Trigger evaluations during pull requests with our GitHub Action.

---

## ⚙️ Core Modules

| Module               | Description                                                             |
| -------------------- | ----------------------------------------------------------------------- |
| **Scenario Builder** | GUI & JSON editor for crafting reusable, multi-turn test presets        |
| **Batch Runner**     | Orchestrates calls to your AI API and scores them using models or logic |
| **Report Viewer**    | Web interface or API to analyze evaluation results                      |
| **GitHub Action**    | Run evaluations automatically on PRs and view results in your pipeline  |
| **Backend API**      | Core logic for evaluation, scoring, and metadata comparison             |

---

## 📦 Project Structure

```bash
levelapp/
├── levelapp-action/         # GitHub Action interface
│   ├── action.yml
│   ├── entrypoint.sh
│   └── README.md
├── levelapp-core/           # Core backend logic (batch engine, scoring, metadata diff)
├── levelapp-scenario-ui/    # Web app to create and manage scenario presets
├── levelapp-report-ui/      # Optional web dashboard to view reports
├── levelapp-docs/           # Markdown and guides
├── examples/                # Example scenarios, evaluations, API calls
└── README.md                # You're here!
```

---

## 🚀 Getting Started

### 🧪 Local Evaluation Example

```bash
curl -X POST https://your-levelapp-host/api/evaluate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "example-multiturn",
    "project_id": "demo-ai-app",
    "attempts": 3,
    "model_name": "gpt-4"
  }'
```

### 🤖 GitHub Action Integration

Include in `.github/workflows/eval.yml`:

```yaml
- name: Run Evaluation
  uses: norma-dev/levelapp-action@main
  with:
    repoToken: ${{ secrets.GITHUB_TOKEN }}
    api_host: "https://your-levelapp-host.com"
    vla_credentials: ${{ secrets.VLA_CREDENTIALS }}
    project_id: "my-ai-app"
    user_id: "qa-user"
    scenario_id: "multi-turn-checkout"
    model_name: "gpt-4"
    test_name: "PR Evaluation"
```

---

## 📊 What Does an Evaluation Look Like?

LevelApp evaluates AI systems using the following structure:

- **Input**: Scenario with multi-turn conversations
- **Execution**: Call the API for each turn, passing context
- **Scoring**:
  - Response similarity (using LLMs or logic)
  - Metadata extraction (accuracy, precision, recall)
  - Guardrail compliance (e.g., should stop, shouldn’t say X)
- **Output**: Report with pass/fail + scoring breakdown

---

## 🔒 Secure Integrations

You can securely integrate:

- 🔐 API credentials for your AI system
- 🔑 LLM keys (OpenAI, Anthropic, IONOS, etc.)
- 🔍 Project and scenario IDs scoped to your repo

Use GitHub Secrets and token-based access for security.

---

## 🛣 Roadmap

| Phase      | Focus                                               |
| ---------- | --------------------------------------------------- |
| ✅ Phase 1 | Open-source GitHub Action + minimal backend support |
| 🔄 Phase 2 | Scenario builder UI and CLI                         |
| 🔄 Phase 3 | Public backend scaffolding with DB schema builder   |
| 🔄 Phase 4 | Dockerized or self-hostable evaluation server       |
| 🔄 Phase 5 | Model plugins, advanced metrics, CI badges          |

---

## 🤝 Contributing

Want to help?

We welcome PRs, feedback, and examples. This is a practical tool designed for real AI workflows — the more we collaborate, the more powerful it becomes.

📬 **Ideas? Bugs?** Open an issue or email us at `opensource@norma.dev`.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for more info.

---

## 👋 About Norma

**Norma** is a tech company building AI-native tools for continuous validation and automation. LevelApp is part of our larger mission to make **AI evaluation as easy and reliable as unit testing.**

[Website](https://www.norma.dev) • [LinkedIn](https://www.linkedin.com/company/norma-dev)
