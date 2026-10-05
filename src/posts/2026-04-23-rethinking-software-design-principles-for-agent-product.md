---
title: "Rethinking Software Design Principles for Agent Product Development"
date: 2026-04-23
description: "Classical principles still hold, but their meaning shifts when the reasoning path is controlled by the model, not the code."
original: "https://medium.com/@piscaries/rethinking-software-design-principles-for-agent-product-development-0b1842c7338e"
---

## **Rethinking Software Design Principles for Agent Product Development**

> *Classical principles still hold, but their meaning shifts when the reasoning path is controlled by the model, not the code.*

Klaviyo Composer is an AI-powered content generation agent. Marketers describe what they want in natural language and Composer produces production-ready campaigns, journeys, templates, and copy exported into Klaviyo or Mailchimp. Every output must meet four constraints simultaneously. It must be structurally valid (schema-enforced JSON that renders in the platform’s editor), platform-aware (Klaviyo and Mailchimp have different capabilities and limits), data-grounded (the company’s own brand voice, audience segments, and images, not generic content), and multi-channel correct (email, SMS, push, and WhatsApp each have their own format constraints).

Generating content that satisfies all four is hard enough for one output. In practice, marketers need to run campaigns across many segments, seasons, channels, and products simultaneously. The volume of content required far exceeds what any team can produce manually. For example, a marketer prompting *“Create spring planting campaigns for fruit plants, tailored to our cold-climate and warm-climate segments”* triggers two generator agents running in parallel, each grounded in the right segment data, brand voice, and channel constraints, returning two production-ready campaigns in one shot.

Handling this complexity requires an agent system, one that reasons about customer-specific context, adapts mid-conversation, and makes judgment calls a fixed workflow cannot. Agent technology is new and open-ended. The ecosystem shifts quarterly and there are no established playbooks. Without shared principles, a team makes inconsistent decisions that compound into design debt and make the system harder to scale.

We started with classical software design principles and found they still hold, but their meaning shifts when the execution is nondeterministic and the reasoning path is controlled by the model, not the code.

This post works through five classical principles and four new ones, each grounded in what we learned building Composer. The classical ones still hold. What changed is how you apply them when a model controls the execution path.

## 1. Single Responsibility → Scope Agents by Context and Behavior

**The traditional view:** One class, one reason to change. One service, one domain. Draw boundaries by responsibility.

Traditional Single Responsibility Principle splits by *responsibility*. The real signal for agents is *information dependency*. “One responsibility per agent” doesn’t tell you where to cut. An agent is designed to handle multiple tasks flexibly. Cut too aggressively, and you fragment context. Cut too little, and the agent drowns in irrelevant tokens. [Anthropic recommends](https://www.anthropic.com/engineering/building-effective-agents) starting with the simplest pattern and adding complexity only when it improves outcomes; Google’s [ADK documentation](https://adk.dev/agents/multi-agents/) structures applications around multi-agent composition. Where you land depends on your product’s information dependencies.

**What still holds:** A component with focused scope is easier to reason about, test, and improve. For agents, this means a focused agent with clear context produces more consistent behavior and is easier to evaluate than one stretched across too many concerns.

**What shifts: scope agents by context and behavior, not by task.** When two tasks share significant context and behave similarly, splitting them fragments information for negligible gain. If they need different data and different instructions, one agent has to carry both, and the system prompt grows to cover cases that are irrelevant to whichever task is actually running.

**Our story:** We started with a single generic generator agent that handled campaigns, templates, images, copy, and journeys. One agent, one prompt, the simplest thing that could work. But as new use cases were added, the system prompt bloated and quality diverged across output types.

We split into a lead-worker architecture. An orchestrator agent handles task understanding, context preparation, and tool filtering, then triggers generator agents parameterized for the specific output type. Each generator receives only the context relevant to its task. The orchestrator can trigger multiple generators in parallel. The spring planting example runs this way, with two generators working simultaneously on different segment data.

Quality improved and per-generation token cost dropped by roughly half. The next question was at what granularity we should split further. We used context and behavior as the guide. A template generation needs block schemas and layout constraints. A campaign generation needs segment data and send timing. A journey generation needs trigger sequences and step dependencies. These are different enough in both data and reasoning that one generic generator carrying all of it meant most context was irrelevant on any given run. We split into specialized agents by output type, with the template agent reused as a subagent by campaign and journey agents when they need email structure.

![](/images/rethinking-software-design-principles-for-agent-product/4e38cdba72.png)

## 2. Separation of Concerns → Draw Clear Boundaries Without Structural Enforcement

**The traditional view:** Each component owns a distinct concern. One concern per component, one component per concern.

**What still holds:** Keep distinct concerns in distinct components. Mixing them creates tech debt in any system. In agent systems, the case is even stronger. Mixed concerns make troubleshooting harder, and they carry a direct runtime cost because every piece of mixed-in knowledge is billed in tokens on every iteration and competes for the model’s attention.

**What shifts:** First, there is no structural enforcement. In software, a private method can’t be called from outside. For agents, multiple mechanisms can serve similar purposes, and nothing prevents you from putting any concern in any of them. Second, debt accumulates silently. Without discipline about which mechanism owns what, concerns duplicate across layers and new features go wherever is easiest. The symptoms (prompt bloat, degraded instruction-following, changes rippling across layers) don’t look like a separation problem until you diagnose them.

**Our story:** Knowledge can reach an agent through three paths: the system prompt (always-on), skills (on-demand, agent-activated), and tools (external calls). Initially we had no clear boundary between them. Everything went into the system prompt, and the prompt grew past the point where the model could follow all of it reliably.

It couldn’t scale. We drew boundaries by understanding the nature of each delivery mechanism and matching them to the right use cases. The following table shows how we think about the separation.

![](/images/rethinking-software-design-principles-for-agent-product/7576236bcd.png)

This discipline matters most as the system grows. Every new channel, integration, or compliance requirement is a piece of knowledge that needs a home. If the default is “add it to the system prompt,” cost and quality both degrade. If each layer has a clear role, new knowledge has an obvious destination.

## 3. Information Hiding → Control What the Agent Can See and Say

**The traditional view:** Hide what callers don’t need. In software, information is hidden by default; a caller only sees what you explicitly expose.

**What still holds:** Only expose what’s needed. The goal is the same. Control what a component can access so you can control what it does.

**What shifts:** In software, hidden information stays hidden. A private field can’t leak into a response. Agents are nondeterministic. If the agent can see it, the agent can include it in the output, paraphrase it, or act on it in ways you didn’t intend. Information hiding for agents is about making the agent respond only with what you want it to. That means controlling both what goes in and what stays in. Don’t pass implementation details, privacy-sensitive data, or terms of service into the context unless you have guardrails that regulate the output. Context also grows with every iteration (tool results, generated artifacts, prior turns). Without active management, the model carries forward everything from the start.

**Our story:** An internal user asked the agent how it generates campaigns and what tools it uses. The agent answered honestly, describing its own implementation details because everything was in the context and the model had no reason to withhold it. That’s the difference from software. A traditional API would never expose its internals through its own response. An agent will, unless you prevent it.

We worked with the product team to define what the agent should and shouldn’t disclose, added guardrails to enforce those boundaries, and incorporated compliance, privacy policy, and terms of service into the agent’s constraints. The lesson was straightforward. If you don’t explicitly define what the agent should hide, it will share whatever it knows.

## 4. Least Privilege → Scope Tool Access, Contain the Execution Environment

**The traditional view:** API keys, IAM roles, access control groups. Identity determines what each service can reach. Least privilege means your identity determines your access, nothing more.

**What still holds:** Don’t grant more access than the task requires. Minimize blast radius when something goes wrong.

**What shifts:** Two levels change. The logical boundary moves from identity-based to capability-based. The same agent engine runs with a different tool pool depending on what the agent is allowed to do. The physical boundary moves from runtime permissions to deployment-time isolation. Agents should run in isolated containers so the execution environment enforces what the agent can reach, independent of what application code permits. Reversibility is a practical guide for how much autonomy to grant. If an action can be undone easily (generating a draft, editing a template), the agent can act on its own. If it can’t be undone (sending a live campaign to real customers, writing to production), require human approval first.

**Our story:** Two decisions shaped how we put this into practice:

- **Label-based and hierarchical tool access control:** Today each agent definition lists the exact tool names it can access. As the tool set grows with new channels and MCP integrations, maintaining those lists becomes brittle. We are moving toward labeling tools by channel, operation, and domain, so access can be granted at the right level of granularity without updating every agent definition when a new tool is added.
- **Stateless containers with limited system access:** Agents deploy to stateless containers. Stateless means no state carries over between turns; each invocation starts clean. Limited system access means the boundary is structural. If the agent tries to reach a production database or another user’s session, the execution environment blocks it regardless.

![](/images/rethinking-software-design-principles-for-agent-product/3a51181966.png)

## 5. Observability → Observe the Reasoning, Not Just the Result

**The traditional view:** Instrument inputs and outputs at service boundaries. If the output is correct, the path was correct.

In agent systems, the same input can produce different execution paths and different results. The context window drives those decisions, but it is invisible by default.

**What still holds:** You need visibility into what the system is doing. In software, that means logs, traces, and metrics at service boundaries. For agents, the same discipline applies.

**What shifts:** You need to observe the reasoning process itself, including what context the model had at each step, what tools it called, and how the context evolved through the loop.

**Our story:** We started where most teams start, evaluating final outputs. If the generated content was correct, the system was working. But in an agent system, a correct output can still take far more iterations than the task required.

We defined strict thresholds on prompt token budget per generation, end-to-end latency, and output quality scores. Then we built tooling to scan traces against these thresholds, inspecting what happened inside the loop on each generation.

The most impactful optimizations came from scanning long-running traces, not from evaluating generated content. By inspecting what happened inside the loop, we found failures that output evaluation would never catch. Tool ordering in the system prompt was affecting which tools the model called first. The agent was regenerating entire outputs when an incremental edit would have been done. Conflicting instructions from multiple sources were causing repeated validation retries. None of these showed up as “bad output.” They showed up as excessive iterations, inflated token counts, and unnecessary latency. Output evaluation alone would never surface them.

## New Principles for Agent Development

Building Composer also revealed principles native to agent systems that don’t directly map to classical software engineering.

**Don’t spend nondeterministic iterations on deterministic things.** Every LLM call costs tokens and latency, and produces a nondeterministic result. If an operation always returns the same output regardless of context, it doesn’t belong inside the agent loop. Loading instructions, routing a request, validating a schema. None of these require reasoning. Extract them before or after the loop and keep the loop focused on decisions that actually need the model.

**Continuously optimize the system around the model.** The model is fixed; everything around it is yours to improve. Context curation, instruction delivery, tool filtering, compaction strategy are all yours to tune, ranging from lightweight changes like tighter prompts and concise tool schemas to heavyweight techniques like agentic RL. Treat it as ongoing work, not a launch milestone.

**Evaluation must cover multiple dimensions.** Agents trade determinism for intelligence, at the cost of more tokens, more latency, and less predictable results. What you can’t control at development time, you must catch at evaluation time. Output quality, cost, latency, execution efficiency, and reliability each have different failure modes and need separate thresholds. These dimensions trade off against each other. Tighter validation improves quality but increases latency. Fewer iterations cut cost but risk lower fidelity. Track all of them and define what regression means for each.

**Build for change.** The AI ecosystem evolves faster than any architecture decision. We abstract the interface between agents and their knowledge sources (skills, tools, MCP integrations) so that when the delivery mechanism changes, the agent prompt does not. When MCP became the standard for tool integration, we updated adapters without touching agent logic. Keep components modular and maintain clear interfaces so the next shift costs a week, not a rewrite.

## Where We Ended Up

Guided by these principles, we built the current version of Composer’s agent system in a couple of months. It’s still early and we’ll continuously expand and optimize as we learn more and the ecosystem evolves. Here’s where we are today:

![](/images/rethinking-software-design-principles-for-agent-product/2e2b0c1a55.png)

## What We Learned

Classical software design principles still apply to agent systems. What doesn’t transfer is applying them with their original meanings and assuming the same solutions follow. The same applies to patterns from Anthropic, Google, and others. They made specific assumptions about the problems they were solving. Before adopting any pattern, understand what problem it was designed for. Agent systems are still early enough that the most useful thing you can bring to the design is a clear understanding of your own constraints, not a borrowed playbook.

## Attachments

To illustrate the campaign generation process, the following screenshots show the production-ready campaigns generated by the system from a single prompt: *“Create spring planting campaigns for fruit plants, tailored to our cold-climate and warm-climate segments.”*

![](/images/rethinking-software-design-principles-for-agent-product/91daf70df2.png)
