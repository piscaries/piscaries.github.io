---
title: "I had Codex and Pi build the same app in Orca, then compared them side by side"
date: 2026-10-05
description: "Two coding-agent teams, one chess coach, matched conditions. Every review passed both; side by side, the gaps were large."
repo: https://github.com/piscaries/codex-vs-pi-in-orca
image: /images/codex-and-pi-build-the-same-app-in-orca/fig2-architecture.png
---

Different coding agents are good at different jobs, and what each one is good at shifts every time its model is updated. Which agent you put on which stage of the work directly shapes the quality of the software you ship. So how do you find out which agent fits which stage?

Tools like Orca and Herdr make that question answerable. They let you assign a different coding agent to each task in one development environment, which also makes it cheap to give two agents the same job and compare them. To show how, I set up a separate coding agent for each stage of development (spec, design, build) and staffed every stage twice: one team ran entirely on Codex, the other entirely on Pi. Both teams built the same app, a chess coach, from the same requirements, prompts and starting code. Then I compared them on two layers:

- **How they built it.** An independent reviewer and blind judges scored each agent's spec, design and code: requirement coverage, soundness, code quality.
- **What they built.** Both apps contain a chess engine, so the two engines played each other, a result no judge has to score.

By the end of this post you will know:

- What Orca is, and how you can use it to build products with a team of coding agents.
- How to find out which of today's agents suits which task.
- How the apps that Codex and Pi each built compare: on hidden tests, coaching, and a head-to-head engine match.

## The setup: two coding-agent teams, matched conditions, one chess problem

Both teams and the shared reviewer ran in Orca, an IDE built for coding agents; the [next section](#how-to-build-and-run-the-two-teams-in-orca) shows how.

The comparison puts two coding-agent teams side by side: one built on Codex, running OpenAI's GPT-5.6 Sol, and one built on Pi, running Z.AI's GLM-5.3. Z.AI benchmarks GLM-5.3 against GPT-5.6 Sol in its own launch results, so the two models are from the same generation. An earlier run used GPT-5.5; it is kept in the [repository](https://github.com/piscaries/codex-vs-pi-in-orca/tree/main/runs/gpt-5.5).

Codex and Claude Code come fully set up around their vendor's models and tools. Pi is a bare agent by design: it starts with four basic tools, works with models from many providers, and leaves the rest to you to configure: prompts, skills, extensions. To keep the test fair, I checked that everything except the agent matched:

| Condition | Codex track | Pi track |
| --- | --- | --- |
| Model | GPT-5.6 Sol | GLM-5.3 (benchmarked by Z.AI against GPT-5.6 Sol) |
| Task text | Identical | Identical |
| Role prompt | Top of the task message | Top of the task message |
| Reasoning effort | High (not its top setting, xhigh) | High (not its top setting, max) |
| Personal configuration | Clean config; Codex's bundled skills, a task-continuity plugin and Orca's status hooks | None; skills off; Orca's status extension |
| Built-in tools | Codex's own: web search, sub-agents, plugins and more (it used only shell commands and two web searches) | read, bash, edit, write |
| Reviewer, judges, hidden tests | Shared | Shared |

This compares two agent-and-model pairs: the agent and the model changed together, so the results cannot say which of the two made the difference.

Both agents get the same project: a chess coach for adult beginners. You play the computer. After each move, the coach tells you in plain words whether it was good and what was better, and at the end it reviews your worst moves. I chose chess for three reasons:

- **It is hard.** Chess rules, a search engine and honest coaching are all easy to get subtly wrong.
- **It is checkable.** Correct rules can be verified against published move counts.
- **The results can compete.** The two engines can play each other, with no judge needed.

**A fair contest gives both agents the same task, the same reviewer and the same settings, and it ends in a result no judge has to score.**

## How to build and run the two teams in Orca

To compare the two agents on real software work, I needed the same multi-agent engineering team twice: once staffed by Codex, once by Pi.

**Orca is an agent development environment: an IDE built for coding agents.** It runs Claude Code, Codex and other coding agents in parallel, each in its own git worktree and terminal, so agents working at the same time never edit the same files; Claude Code, Codex and Pi shared one window for this project. Orca also records the work as a Run (the whole job), Tasks (its pieces) and Dispatches (attempts at a task). A coordinator dispatches tasks, workers report back when they finish, and a worker can stop and ask the coordinator a question.

![Orca with the Codex team's spec worktree, annotated](/images/codex-and-pi-build-the-same-app-in-orca/fig1-orca-annotated.png)

*Figure 1. Orca with the Codex team's spec task: its own worktree and terminal, and Codex reporting back to the coordinator. Unrelated items are blurred.*

**The architecture is built for the comparison.** The two teams are identical except for the author agent: same roles, same flow, one shared reviewer. The judging sits outside both teams.

![Two identical teams in Orca, one per agent, with a shared reviewer between them; two blind judges score the specs, designs and finished apps, and both finished apps go through hidden tests, a coaching comparison, an engine match and an acceptance review.](/images/codex-and-pi-build-the-same-app-in-orca/fig2-architecture.png)

*Figure 2. The two teams differ only in the author agent. The reviewer sits between them; everything orange happens outside both teams.*

| Role | Codex team | Pi team |
| --- | --- | --- |
| Product designer: writes the spec | Codex (GPT-5.6 Sol) | Pi (GLM-5.3) |
| Engineering designer: writes the design and build plan | Codex | Pi |
| Builder: implements one phase at a time | Codex | Pi |
| Code reviewer and acceptance reviewer | Claude Code (Claude Opus 4.6) | Claude Code (Claude Opus 4.6) |
| Coordinator: assigns work, answers questions | me, through Orca | me, through Orca |

**How a team is launched.** Each role is a short prompt file that says how to do the job, what the output must look like and when it is done. A shared charter, `TEAM.md`, sets the rules: work only in your own files, report only checks you actually ran, and ask instead of guessing. Here is the start of the builder's file, open in Orca:

![The builder's role file open in Orca](/images/codex-and-pi-build-the-same-app-in-orca/fig3-builder-prompt.png)

*Figure 3. The builder's role file, open in Orca. Every role is a file like this in prompts/team/ (right), published as [team/](https://github.com/piscaries/codex-vs-pi-in-orca/tree/main/team) in the repository.*

Each team works on its own branch, and both branches start from the same commit, with no chess code in it. For every task, Orca creates a fresh worktree and terminal, and a launch script starts the agent with the settings from the fairness table.

The charter, the role file and the task then go to the agent as one message with `orca orchestration worker-start`.

**How a team runs.** Both teams follow the same reviewed steps: spec, review, design, review, then the build, one phase at a time. Codex's design split the build into five phases; Pi's split it into six. Every phase goes to a new reviewer session: REWORK sends it back, PASS merges it into the team's branch. When an agent asks a question, I answer it as the coordinator.

Orca records every task in the Run. Here is the Codex team's, from `orca orchestration task-list`:

```text
task_11d4deb17dca [completed] t3 spec
task_00bd0eb480d4 [completed] t3 spec review
task_20b40a9707ed [completed] t3 design
task_c06515b888ae [completed] t3 design review
task_139320b8ec8c [completed] t3 build P0
task_70a5ee00f59e [completed] t3 code review P0
task_fdf015a5ba05 [completed] t3 build P1
task_b3266b5137e5 [completed] t3 code review P1
task_fc3fa6d33368 [completed] t3 build P2
task_18800831512e [completed] t3 code review P2
task_3333bdb35a88 [completed] t3 build P3
task_682619f0e842 [completed] t3 code review P3
task_7a006755404b [completed] t3 build P4
task_331cf6f00cd8 [completed] t3 code review P4
task_65f1c06cb47a [completed] t3 acceptance
```

**How the teams are compared.** On two layers, with the reviews and the scoring done blind:

- **How they built it.** The reviewer checks each team's spec, design and code on its own, and is given only a track label, though Codex's own handoff notes named its model family. Each agent's own logs supply the working time and token counts.
- **What they built.** Both finished apps run 43 acceptance tests that no agent ever saw, written and fingerprinted before the run. Then I compare their coaching on the same positions, and the two chess engines play each other. A final acceptance review plays full games in each app as a beginner would.
- **Blind judges, across both layers.** Two strong judges, Claude Opus 5.5 and GPT-6.1 Sol, score the two specs, the two designs and the two finished apps side by side as A and B, with anything that could identify the author removed. Each rubric is split between general engineering practice and what this product needs: correct rules, a strong engine, truthful coaching and a responsive page. For the finished apps, the judges run both, test them, and play the two engines against each other. I wrote this rubric after an earlier, generic one had failed to tell the two engines apart; both teams were scored against the same rubric, and the judges never saw the match results.

With both teams built and run to the end, the results in short:

- With the same task, prompts and reviewer, Codex (GPT-5.6 Sol) finished in under a quarter of Pi's time; Pi (GLM-5.3) built the far stronger chess engine.
- Both apps passed all 43 hidden tests, yet in a 20-game match Pi's engine won 18 and drew 2 against Codex's.
- Reviewed one at a time, every spec, design and code change passed. Side by side, blind judges and measurements found what single reviews missed: a weak engine, a page that freezes, boards drawn wrong.

The sections below go through each layer, starting with how each team worked.

## Codex builds four times faster

Codex's team finished in under a quarter of Pi's time, at a similar cost. Neither build had a time limit, so how long to spend was each agent's own choice.

|  | Codex | Pi |
| --- | --- | --- |
| Working time: spec / design / build | **48 min** (4 / 5 / 40) | 217 min (7 / 4 / 207) |
| Tokens used (of which output, incl. reasoning) | **10.8 million** (150,000) | 32.0 million (541,000) |
| Equivalent API cost at list prices | **$9.24** | $11.42 |
| Code reviews passed first time | 5 of 5 | 6 of 6 |

Both agents ran on subscriptions (ChatGPT for Codex, Z.AI's GLM Coding Plan for Pi), so the like-for-like figure is the API cost at list prices: $4, $0.40 and $20 per million input, cached-input and output tokens for GPT-5.6 Sol, against $1.40, $0.26 and $4.40 for GLM-5.3. At GPT-5.6 Sol's launch price, before an August price cut, Codex's run would have cost $12.31. Pi used three times the tokens at a much lower price per token. Its working time includes about 13 minutes spent waiting for me to answer a question.

The two agents also asked for help differently. Codex asked three questions: how to treat input the spec left undefined, whether to correct a test position it had written wrongly, and what to do about a test command from its own plan that did not run. Pi asked two. Midway through the build, it measured that a coach comment plus the computer's reply took about 2.45 seconds, over the spec's 2-second limit, and asked to cut the coach's time budget from 1.2 to 0.5 seconds. Later it asked to edit a file outside its phase.

**What the judges saw.** The reviewer, seeing each design alone, scored them 88 and 87 and accepted both. Side by side, the two strong judges split on the specs and designs: Opus 5.5 preferred Pi's, GPT-6.1 Sol preferred Codex's. They agreed on two things specific to a chess coach: Pi had planned the stronger engine, with a fuller search and evaluation, and Codex the more responsive page, with its search in a background worker. The finished apps bore out both (next section). On coaching they split.

### What the AI reviewers missed

Every code review passed, and both acceptance reviews rated the board as clear. Yet both boards have rows of uneven height, and Pi's colors are reversed. I found this only by measuring the page (Figure 4). The judges, scoring the finished apps side by side, found two more: Pi's page stalls for half a second or more while the computer thinks, because its search runs on the page's main thread, and Codex's level-weakening noise has no effect. A single review asks whether a change is good enough; only side by side do the gaps show.

## Pi's engine beats Codex's: 18 wins, 2 draws, no losses

Start with a look. Here are both apps after the same moves: 1.e4 d5 (the computer answered d5 in both), then a deliberate blunder, 2.Ba6, which leaves the bishop hanging.

![Both chess coaches after 1.e4 d5 2.Ba6, with the board defects marked](/images/codex-and-pi-build-the-same-app-in-orca/fig4-apps-side-by-side.png)

*Figure 4. Both apps after 1.e4 d5 2.Ba6. Both coaches flag the hanging bishop; Pi's explains it in plainer words. The red marks show board defects that no AI reviewer reported: rows of unequal height on both boards, and Pi's light and dark squares the wrong way round.*

- **Codex's coach** says "Your opponent can capture your bishop on a6 with their pawn from b7. Try move from b1 to c3." It names the pieces, but gives the better move as squares rather than naming the piece.
- **Pi's coach** names the pawn that captures, notes that nothing can take it back, and gives the better move in plain words. Pi's app also lets you play Black.

Both engines are correct: each passed all 43 hidden tests. The tests check the rules, but they cannot say which app is better. Two things can.

**Pi coaches better.** On the same positions:

| Position | Codex's coach | Pi's coach |
| --- | --- | --- |
| Queen moved where a pawn takes it | "Your opponent can capture your queen on d4 with their pawn from c5." | "Your queen on d4 can now be captured for free by the pawn on c5. A stronger move was moving your queen from d1 to d5." |
| Checkmating move | "That was the strongest move." | "Checkmate — you win the game." |
| Weak first move, 1.g4 | Rated best | Rated an inaccuracy; suggests developing the knight |
| Time per comment | 30–351 ms | about 500 ms |

**Pi's engine is far stronger.** The two engines played 20 games: 10 fixed openings, each side playing White once, 200 milliseconds per move. Pi won 18, every one by checkmate, and drew the other 2. Codex won none. Counting a draw as half a point, that is 19–1.

![Game 15, mid-game and final position](/images/codex-and-pi-build-the-same-app-in-orca/fig5-match.png)

*Figure 5. Game 15, Codex playing White. At mid-game the material is level; Pi (Black) finishes with mate on d1.*

A result this lopsided invites doubt, so I checked what could have tilted it. Neither app contains third-party code, and both engines were frozen before the match and played through my own script, with no agent involved. Each move had the same 200 ms, and Pi used less of it. The first match used Codex's rules as referee; with Pi's rules and a full second per move, a second 20-game match still went to Pi, 13 wins and 7 draws (16.5–3.5), and every blind judge's own games went to Pi too. The full logs are in the [repository](https://github.com/piscaries/codex-vs-pi-in-orca).

## Conclusion

Different coding agents are good at different jobs, and the reliable way to know which fits which stage is to compare them on your own work. Orca makes that practical: I defined one engineering team as plain role files and ran it twice, once on Codex and once on Pi. Codex finished in under a quarter of the time; Pi built the better chess coach. Reviewed one at a time, both teams passed every check; the gaps showed up only side by side.

Two lessons about the method itself. **Compare models of the same generation**, or the result may only show which model is newer. **Judge the product, not just the plans, with criteria specific to it:** general engineering criteria could not tell a strong engine from a weak one.

Pi with GLM-5.3 deserves a closer look. On this project it built a better product than Codex with GPT-5.6 Sol, and it is well worth trying in your own development.

These results come from one project. **The method is the part to keep:** each time a new model or coding agent comes out, **try it side by side with your current one on a few tasks from your own projects.** That tells you more than reported scores about what it brings to your work.

*Everything behind this post, from the prompts and task messages to both apps, the hidden tests and the match logs, is in the [repository](https://github.com/piscaries/codex-vs-pi-in-orca), along with a step-by-step [reproduction guide](https://github.com/piscaries/codex-vs-pi-in-orca/blob/main/REPRODUCE.md). This is a follow-up to an [earlier experiment](/posts/can-open-source-coding-agents-build-comparable-software-for/) with open-source coding agents.*
