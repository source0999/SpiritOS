# SpiritOS Scout Design Intake Bridge v0.1

Status: manual-gated bridge plan only, no Scout runtime integration

This document defines a future bridge between Scout and the Design Vault. It does not change Scout runtime behavior, add crawler behavior, approve sources, extract design references, write to coding context, or alter Source Proxy or Cartographer authority.

## Purpose

Scout may eventually help identify candidate design references for human review. In v0.1, Scout remains a candidate suggestion lane only. Design Vault approval remains manual and source-card based.

## Current Scout Boundary

The existing Scout v0.4 closeout states that Scout can expose gates, candidates, packet review, discovery state, promotion queue metadata, and safety state. It also states that Scout must not auto-approve sources, activate sources without human approval, write to proxy memory automatically, write to coding context automatically, or execute code changes.

This design bridge keeps that boundary.

## Allowed Future Flow

1. Scout identifies or displays a candidate design reference.
2. A human reviews the candidate.
3. A human chooses whether to create a Design Vault source-card draft.
4. The source card remains draft until approved.
5. Only approved source cards may be analyzed by Reverse Designer or used by Design Blender.
6. Design packs remain proposal evidence only.
7. Source Proxy approval is required before any app UI write.

## Forbidden In v0.1

- automated web crawling
- Scout auto-approval of design sources
- Scout auto-rejection or auto-blocking of design sources
- Scout auto-promotion into Design Vault
- Scout auto-promotion into coding context
- Scout writing design packets to proxy memory automatically
- Scout triggering Reverse Designer analysis automatically
- Scout triggering Design Blender output automatically
- Scout creating Source Proxy implementation proposals automatically
- any app UI writes

## Candidate Suggestion Contract

A future Scout design candidate should be treated as unapproved metadata.

Suggested candidate fields:

- candidate id
- title
- source URI or local path
- source type
- discovered by
- discovery reason
- risk notes
- suggested use mode
- human review status
- linked source-card id, if created

Candidate metadata is not approval.

## Manual Promotion To Source Card

Manual promotion means:

- a human intentionally selects a candidate
- a source-card draft is created
- rights basis is recorded
- disallowed assets are recorded
- approved use mode is chosen by a human
- reviewer and reviewed date are recorded

No candidate becomes approved without source-card approval.

## Design Vault Boundary

Design Vault remains the system of record for design reference approval.

Scout may suggest. Design Vault records. Reverse Designer analyzes only approved inputs. Design Blender blends only approved inputs. Source Proxy applies only after explicit implementation approval.

## Coding Context Boundary

Scout must not auto-promote design packets into coding context.

Allowed later:

- human-reviewed design pack link
- human-approved source-card link
- human-approved proposal evidence summary

Not allowed:

- automatic coding task creation
- automatic diff generation
- automatic Source Proxy approval
- automatic app UI writes

## First Safe Integration

The first future integration should be read-only and manual:

- show a Design Vault source-card draft link beside a Scout candidate
- do not create it automatically
- do not approve it automatically
- do not extract it automatically
- do not promote it automatically

## Checks Before Any Implementation

Before implementing this bridge later:

1. Confirm Scout v0.4 safety boundaries still hold.
2. Confirm Design Vault source-card schema is stable enough.
3. Confirm no crawler behavior is being added.
4. Confirm no coding-context promotion is automatic.
5. Confirm Source Proxy remains the only app-write lane.
6. Confirm Cartographer authority is unchanged.
