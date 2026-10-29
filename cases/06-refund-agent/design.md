# Case 06: A Support Agent That Can Issue Refunds

**Cloud:** AWS · **Status:** Design (ADRs proposed), post ready · **Blog post:** *A Support Agent That Can Issue Refunds: The Model Proposes, the Customer Confirms* (`post.md`)

> Composite scenario on synthetic data. Numbers are planning figures, not benchmark results.
> Reuses Case 02 (task-token review queue; random audit of automatic decisions) and Case 05 (release gate). Prompt injection is left for a later post.

![Cover](images/00-cover.png)

## 1. Problem

Online home-goods retailer: ~40,000 support conversations a month, ~20% refund requests, mostly small and clear-cut. Human agents take ~4 minutes per refund; customers wait about a day.

Prototype: agent with `get_order(order_id)` and `issue_refund(order_id, amount, reason)` using a service account that can see every order. A red-team week found:
1. Refund of another customer's order ("I'm helping my mother with order 88412").
2. Double refund after a timeout and retry.
3. Refund above order value ("courier promised refund + shipping + 20%").

**Core problem:** the design let the model decide who the customer is, whether a refund already happened, and how much money to send.

![Red-team week](images/01-red-team-week.png)

## 2. Requirements

![Requirements](images/t1-requirements.png)

**Must never go wrong**
- Only the signed-in customer's orders can be refunded.
- The same items are never refunded twice.
- The amount never exceeds what the rules allow.

**Functional**
- Eligible refunds up to $150 resolved in minutes.
- Others go to a person (target four hours).
- Customer confirms every refund with a UI action.

**Non-functional**
- Total automatic exposure bounded (daily cap, kill switch).
- Every proposal, approval and commit auditable.

**Out of scope:** returns logistics, chargebacks, cross-account fraud detection (separate system).

## 3. Architecture

![Architecture](images/02-architecture.png)

```
Customer (Cognito session) ──chat──► Support agent (AgentCore Runtime)
                                         │ tool calls (identity from session)
                                         ▼
                                 AgentCore Gateway + Policy (Cedar, default deny)
                                   ├─ list_my_orders / get_my_order ──► Orders API (filtered by customer)
                                   └─ propose_refund ──► Refund service ──► quote (ready | needs_approval)
Chat UI ── [Confirm refund] click ──────────────────────► Refund service.commit(quote_id)
                                                           ├─ re-check rules + expiry
                                                           └─ Payment provider (idempotency key = quote_id)
needs_approval ──► Step Functions (task token) ──► support lead review UI ──► commit or decline
All steps ──► audit log (DynamoDB + S3)
```

| Component | AWS service | Responsibility |
|---|---|---|
| Sign-in | Amazon Cognito | Verified customer identity for the chat session |
| Agent | Amazon Bedrock AgentCore Runtime + a Bedrock model | Conversation, tool use, explanations |
| Tool access | AgentCore Gateway | Exposes three tools; passes caller identity |
| Tool policy | AgentCore Policy (Cedar; GA March 2026) | Default deny; allow three tools; reason code allow-list |
| Refund service | Lambda + DynamoDB | Rules, amount, quotes, limits, commit, idempotency |
| Approvals | Step Functions (`.waitForTaskToken`) + review UI | Human decision above limits |
| Payment | External provider | Refund with idempotency key |
| Audit | DynamoDB + S3 | Proposals, commits, approvals, rules evaluated |
| Monitoring | CloudWatch | Daily total, anomaly alarms, kill switch |

## 4. Key decisions

| ADR | Decision |
|---|---|
| [ADR-001](adr/ADR-001-identity-from-session.md) | Customer identity comes from the session; tools filter by it |
| [ADR-002](adr/ADR-002-narrow-tools-no-amount-parameter.md) | Narrow tools; reason codes; the amount is never a model parameter |
| [ADR-003](adr/ADR-003-rules-in-service-policy-at-gateway.md) | Refund rules in the refund service; AgentCore Policy at the gateway as a second check |
| [ADR-004](adr/ADR-004-propose-confirm-commit.md) | Propose, confirm, commit; customer click commits; quote ID as idempotency key |
| [ADR-005](adr/ADR-005-human-approval-above-limits.md) | Above limits, a person decides via a task-token queue |
| [ADR-006](adr/ADR-006-blast-radius-limits.md) | Per-refund, per-customer and daily caps; kill switch; 2% audit |

![Tools](images/t2-tools.png)
![Rules](images/t3-refund-rules.png)
![Propose, confirm, commit](images/03-propose-confirm-commit.png)
![Limits](images/04-limits.png)

## 5. Quote record

```
quote_id, customer_id, order_id, lines[], amount, currency, reason,
status (ready | needs_approval | committed | declined | expired),
rules_evaluated[], created_at, expires_at, confirmed_by, committed_at,
payment_ref, conversation_id
```

## 6. Planning numbers

| | Before | After |
|---|---|---|
| Refund requests / month | ~8,000 | ~8,000 |
| Resolved automatically | 0% | ~70% |
| Sent to a person | 100% | ~18% |
| Declined with explanation | — | ~12% |
| Time to refund (automatic) | ~1 day | minutes |

## 7. Testing

![Scenario tests](images/t4-tests.png)

- Golden set of scenarios scored on tool calls and final state (Case 05 gate), plus text quality separately.
- 2% random audit of automatic refunds (escaped wrongful-refund rate).

## 8. Risks

![Risks](images/t5-risks.png)

## 9. At 10x

- Daily cap becomes a rate per hour and region.
- Cross-account fraud model outside the agent.
- Staffing model for the approval queue.

## 10. Open questions

- Exact limits ($150, 3 in 90 days, $8,000/day) to be agreed with finance and support.
- Whether the kill switch is automatic on anomaly or manual only.
- Retention period for conversation transcripts linked to refunds.
