# Future Hause — Documentation Index

This folder contains the authoritative contracts, constraints, and reference
documents for the Future Hause system.

Not all documents are equal. This index defines **what is binding** vs **what is reference**.

---

## 🟢 Authoritative Contracts (Must Be Obeyed)

These documents define system boundaries and may not be violated by future work.

- **ARCHITECTURE.md**  
  Core system architecture, authority model, and autonomy constraints.

- **fh-constitution.md**  
  Foundational principles and non-negotiable rules.

- **AGENT_CONTRACTS.md**  
  What agents are allowed and forbidden to do.

- **review_agent_contract_v1.md**  
  Explicit limits of review agents.

- **UI_LOCK.md**  
  UI invariants and protected behaviors.

If a proposal conflicts with any document above, the proposal is invalid.

---

## 🟡 Execution & Runtime Design (Supporting)

These documents explain _how_ the system operates within the contracts.

- agent_architecture_and_invocation_v1.md
- intelligence_pipeline_v0.md
- intelligence_contract_v0.md
- llm-routing.md
- events.md
- dashboard_panels.yaml
- animation_states.yaml

These may evolve, but must remain compliant with the authoritative contracts.

---

## 🔵 Planning / Reference (Non-Binding)

These documents capture ideas, plans, or historical context.

- roadmap.md
- INGESTION_PLAN.md
- PROPOSAL_presence_rail.md
- rag_rollout_plan_v1.md
- rag_spec_v1.md
- ui_state_contract.md
- ui_states.md
- CLAUDE_HANDOFF.md

These documents do **not** grant permission or authority.

---

## Final Rule

**Architecture > implementation.  
Contracts > convenience.  
Humans retain final authority.**

This index is itself authoritative.
