# NetSega AI

## AI-Powered Network Fault Diagnosis with Human Review

NetSega AI is an intelligent network troubleshooting system designed to diagnose common network faults using a combination of deterministic rule checking, Gemini AI-based diagnosis, and human review.

The system analyzes network symptoms, topology information, and command/test outputs to identify possible faults, provide evidence-based diagnoses, suggest verification commands and fixes, and maintain a Responsible AI review log.

---

## Problem Statement

Network troubleshooting often requires analyzing multiple configuration and diagnostic outputs such as IP addresses, subnet masks, VLANs, interfaces, DHCP, DNS, and application services.

Manual diagnosis can be time-consuming and may lead to inconsistent results.

NetSega AI provides a structured workflow that combines:

- Deterministic rule-based verification
- AI-assisted diagnosis
- Evidence-based reasoning
- Human review
- Responsible AI logging
- Dashboard-based monitoring

---

## System Workflow

```text
Network Case
     |
     v
Rule Checker
     |
     v
Gemini AI Diagnosis
     |
     v
Human Review
     |
     v
Responsible AI Log
     |
     v
Dashboard