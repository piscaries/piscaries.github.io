---
title: "Can Open Source Coding Agents Build Comparable Software for Less?"
date: 2026-08-03
description: "Coding agents such as Claude Code and Codex can handle much of the work from planning through testing, but heavy model usage can be expensive."
original: "https://medium.com/@piscaries/can-open-coding-agents-build-comparable-software-for-less-f91b9aa450f7"
---

![](/images/can-open-source-coding-agents-build-comparable-software-for/3862afabb7.png)

## **1. Open alternatives to commercial coding agents**

Coding agents such as Claude Code and Codex can handle much of the work from planning through testing, but heavy model usage can be expensive.

Open-source coding agents offer another route. Teams can choose the agent harness and model separately. The field is moving quickly. [OpenCode](https://github.com/anomalyco/opencode) was publicly announced in June 2025, and [Grok Build](https://github.com/xai-org/grok-build) published its source in July 2026. Options from China include [Qwen Code](https://github.com/QwenLM/qwen-code), [Trae Agent](https://github.com/bytedance/trae-agent), and [Kimi Code](https://github.com/MoonshotAI/kimi-code).

That led me to a practical question:

> Can an open source coding agent paired with an open model deliver useful software at a lower cost than Claude Code or Codex?

To test that question, I asked three coding-agent stacks to build the same product independently:  
1. Grok Build + GLM 5.2  
2. OpenCode + GLM 5.2  
3. Claude Code + Opus 4.6/4.8  
to independently build the same product: a technical blog writer that researches GitHub repositories, lets the user approve the evidence, and then plans and generates a cited article.

To make this single-task build by three coding agents as objective as possible, I defined one common task using Codex, outside all three participating stacks, to implement both the benchmark task and a separate deterministic code-quality evaluator. These details will be shared in section 2.

The autonomous-product results were encouraging:

- All three stacks produced working applications and passed the benchmark’s objective workflow gates.
- Claude Code built faster and used fewer model calls and tokens, while the two open stacks had lower estimated model costs.
- The open-stack applications matched or exceeded the Claude Code application across all five measured quality dimensions.

The benchmarks, generated applications, recorded metrics, code-quality evaluator, and reproduction instructions are available in the [open-source repository](https://github.com/piscaries/open-coding-agent-build-study).

------------------------------------------------------------------------

## **2. Experiment design: one product, two build modes, and an independent evaluator**

### **2.1 Choosing a product that is challenging but buildable**

I chose a technical blog writer for coding agents to build, because it sits between a toy task and an open-ended enterprise project. A tiny coding exercise would not distinguish capable stacks. A large system would require repeated product decisions and human clarification, undermining an independent comparison.

The product was a local, single-user application that turns a writing idea into a cited technical article grounded in GitHub evidence. It had to:

- research relevant repositories through the supplied GitHub gateway;
- let the user review and approve the evidence;
- plan and generate the article with a fixed runtime model; and
- provide a browser workflow with deterministic end-to-end tests.

This scope was large enough to test full-stack engineering, tool integration, prompt design, and evidence safety, but bounded enough for one independent build.

### 2.2 Keeping the comparison consistent and independent

A coding agent’s results can be shaped by both human guidance and the environment it works in. To make the comparison reflect differences between the stacks — not differences in operator help, tools, or setup — I kept these factors as consistent as possible:

- Every stack received the same task, platform, dependencies, runtime model, research gateway, and development tools within each mode.
- Every run started in a fresh Docker sandbox containing only its assigned coding agent.
- After implementation began, I monitored the run but did not help write or repair the software.
- The harness recorded time, model calls, tokens, costs, source code, logs, and verification evidence.

### 2.3 Two benchmark modes: specified architecture and autonomous product

I also tested how much engineering freedom the agents could handle. The same product was built in two modes of freedom. Both modes provided the same product goal, expected outcomes, fixed platform, dependencies, and development tools. They differed in how much of the solution was already designed:

1.  **Specified-architecture build:** The agent also received the application architecture, UI framework, contracts, schemas, code structure, and scaffolding. Its job was to implement the missing product logic.
2.  **Autonomous-product build:** The agent received no predefined architecture or code structure. It had to define the product scope, design the application, and implement the complete solution.

![](/images/can-open-source-coding-agents-build-comparable-software-for/5833fce9b0.png)

### 2.4 Build performance: implementation time and builder-model cost

I define **build performance** as total implementation time and builder-model cost. Model calls and tokens provide supporting evidence about the model activity behind those two outcomes.

![](/images/can-open-source-coding-agents-build-comparable-software-for/3ffa0de420.png)

- **Specified-architecture build:** Claude Code finished in 52m 42s, compared with 56m 18s for Grok Build and 61m 18s for OpenCode. The two GLM builds had retrospective API-equivalent cost estimates of \$5.31–\$5.61, 55–57% below Claude Code’s reported \$12.36.
- **Autonomous-product build:** Claude Code finished in 15m 41s, roughly half the 28m 11s–32m 17s used by the two open-agent stacks. The GLM builds cost an estimated \$2.32–\$2.43, 35–38% below Claude Code’s reported \$3.75.

All times measure implementation wall time. GLM costs are estimates based on frozen July 31, 2026 prices, while Claude costs are reported by Claude Code.

### 2.5 Evaluating delivered code quality independently

Build time and model cost tell only part of the story. I also wanted to know whether each stack delivered high-quality code. To evaluate that independently, I used Codex to build a separate deterministic code-quality evaluator for the three autonomous-product applications. The evaluator was developed outside the participating stacks and applied the same checks and browser scenarios across five dimensions:

- Requirements completeness
- Functional correctness
- Maintainability
- Security
- Usability

Each dimension is scored from 0 to 100; the evaluator does not calculate an aggregate winner score. It preserves the evidence behind every score. Test results and source-code counts are direct observations, while several maintainability and usability scores use evaluator-defined heuristics.

![](/images/can-open-source-coding-agents-build-comparable-software-for/6d47c96f8d.png)

*\- **Open-agent results:** For this specific autonomous-product build, both open-agent applications scored higher than the Claude Code application on maintainability and matched or exceeded it on every other dimension.*
- **Claude Code correctness:** The TypeScript check could not resolve a CSS import, reducing the score to 92, although the build, tests, and browser workflows all passed.  
- **Claude Code maintainability:** The score of 43 reflected the same type-check failure, 39 unsafe TypeScript escapes such as \`any\` across 1,757 production lines, and high branch-token density. Its duplication and module-size checks passed.

These scores compare one frozen application per stack under one consistent rubric. They are not a general ranking: another task — or another run of the same task — could produce different results.

------------------------------------------------------------------------

## 3. Open source coding stacks are now a practical option

This experiment gives a scoped yes to both questions:

> **Can an open source** **coding stack deliver useful software at lower model cost?**

For this product, Grok Build + GLM 5.2 and OpenCode + GLM 5.2 delivered working software at lower estimated builder-model cost than Claude Code + Opus 4.8. Claude Code remained faster and used fewer calls and tokens.

> **Can open source** **coding agents build under different levels of engineering freedom?**

Both open-agent stacks succeeded when implementing within a supplied architecture and when designing an autonomous solution from a product vision.

**These findings can deliver substantial benefits to two groups:**

1.  **Enterprises:**  
     — **Lower AI development costs**: Open source coding agents paired with open models can reduce the cost of AI-assisted software development, whether the model is accessed through a managed API or hosted internally.  
     — **Better protection for enterprise data and intellectual property:** Running an open source coding agent internally gives enterprises more control over repository and document access instead of granting a commercial coding-agent service broad access to sensitive assets. When the open model is also self-hosted, source code, documents, prompts, business-domain knowledge, and engineering practices can remain within the enterprise security boundary.
2.  **Individual developers:**  
     — Open source coding agents and open models lower the financial barrier between an idea and working software.  
     — This expanded access matters especially to students and developers in regions where commercial coding-agent subscriptions are difficult to afford.

In summary, this experiment showed that open source coding agents paired with an open model could deliver working, high-quality software for one product at lower estimated model cost. **It does not prove that open stacks are universally better.** However, the result is meaningful: open source coding stacks deserve serious consideration by enterprises and individual developers choosing how to build software with AI.

------------------------------------------------------------------------

## 4. Appendix: Screenshots of the three autonomous-product applications

The screenshots below show the starting page and generated article from each autonomous-product build. They offer a quick look at how the three coding agents interpreted the same product vision and designed the user experience.

To inspect the generated code or run the applications yourself, follow the instructions in the [open-source repository](https://github.com/piscaries/open-coding-agent-build-study).

### Grok Build + GLM 5.2

- **Starting page**

![](/images/can-open-source-coding-agents-build-comparable-software-for/a520cae793.png)

- **Generated article**

![](/images/can-open-source-coding-agents-build-comparable-software-for/e2206afce3.png)

### OpenCode + GLM 5.2

- **Starting page**

![](/images/can-open-source-coding-agents-build-comparable-software-for/1de80c6948.png)

- **Generated article**

![](/images/can-open-source-coding-agents-build-comparable-software-for/77324a6b5d.png)

### Claude Code + Opus 4.8

- **Starting page**

![](/images/can-open-source-coding-agents-build-comparable-software-for/a585ce243f.png)

- **Generated article**

![](/images/can-open-source-coding-agents-build-comparable-software-for/c8cb8cfa2e.png)
