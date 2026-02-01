# Pattern Types

Emergent patterns detected during vault analysis.

## undefined_concept

A term or concept mentioned multiple times across notes but lacking its own dedicated note.

**Threshold**: ≥3 mentions without existing note
**Action**: Propose creating a definition note

## link_cluster

A group of notes that are densely interconnected with each other.

**Threshold**: ≥3 notes with link density >0.5
**Action**: Propose creating a Map of Content (MOC)

## trending_topic

A term appearing with significantly increased frequency in recent content.

**Threshold**: ≥3x baseline frequency in last 30 days
**Action**: Flag as emerging interest area

## hub

A note with unusually high connectivity (inbound + outbound links).

**Threshold**: Total connections >10 or top 5% of vault
**Action**: Consider if this should be a MOC or needs refactoring
