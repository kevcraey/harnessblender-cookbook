# Discovery Engine Examples

Concrete examples van hoe de discovery engine werkt in verschillende scenarios.

## Example 1: Distance-1 Stub Detection

**Input note**: `attention-mechanism.md`

**Note content**:
```markdown
---
title: Attention Mechanism
tags: AI/neural-networks
related-to: [[Transformers]], [[Neural Networks]]
---

The attention mechanism allows models to focus on relevant parts of input.
It uses three components: Query, Key, Value.

Multi-head attention improves this by running multiple attention operations in parallel.
See also [[Positional Encoding]] for sequence position handling.
```

**Discovery process**:

1. **Extract links**: `[[Transformers]]`, `[[Neural Networks]]`, `[[Positional Encoding]]`
2. **Extract related-to**: `[[Transformers]]`, `[[Neural Networks]]` (already in links)
3. **Check each link**:
   - `[[Transformers]]`: exists, 2000 words → NOT stub
   - `[[Neural Networks]]`: exists, 500 words → NOT stub
   - `[[Positional Encoding]]`: exists, 45 words → IS STUB (score: 40)
4. **Broken links**: none found
5. **Semantic gaps**: Extract capitalized terms: "Query", "Key", "Value", "Multi-head attention"
   - Check: `[[Query Key Value]]` doesn't exist → kandidaat (score: 30)
   - Check: `[[Multi-head Attention]]` doesn't exist → kandidaat (score: 30)

**Candidates found**: 3 (enough, skip fallback)

**Scoring** (simplified):
1. `[[Positional Encoding]]` - stub: 40 + mention: 5 + stub_quality: 15 = 60
2. `[[Multi-head Attention]]` - semantic: 30 + mention: 10 = 40
3. `[[Query Key Value]]` - semantic: 30 + mention: 5 = 35

**Learning values**:
1. Read `positional-encoding.md` stub → "begrijp hoe transformers positie-informatie encoderen"
2. Context: "improves this by running multiple" → "begrijp hoe multi-head attention parallel attention operations combineert"
3. Context: "uses three components" → "begrijp wat Query, Key en Value representeren in attention"

**Output**:
```markdown
### Verken verder
1. [[Positional Encoding]] - begrijp hoe transformers positie-informatie encoderen
2. [[Multi-head Attention]] - begrijp hoe multi-head attention parallel attention operations combineert
3. [[Query Key Value]] - begrijp wat Query, Key en Value representeren in attention
```

## Example 2: Broken Link Detection

**Input note**: `reinforcement-learning.md`

**Note content**:
```markdown
---
title: Reinforcement Learning
tags: AI/RL
---

Reinforcement learning trains agents through reward signals.
The [[Bellman Equation]] is fundamental for value estimation.

Common algorithms include [[Q-Learning]] and [[Policy Gradients]].
```

**Discovery process**:

1. **Extract links**: `[[Bellman Equation]]`, `[[Q-Learning]]`, `[[Policy Gradients]]`
2. **Check each link**:
   - `[[Bellman Equation]]`: does NOT exist → BROKEN LINK (score: 35)
   - `[[Q-Learning]]`: does NOT exist → BROKEN LINK (score: 35)
   - `[[Policy Gradients]]`: does NOT exist → BROKEN LINK (score: 35)

**Candidates found**: 3 (enough, skip fallback)

**Scoring**:
1. `[[Bellman Equation]]` - broken: 35 + mention: 5 = 40
2. `[[Q-Learning]]` - broken: 35 + mention: 5 = 40
3. `[[Policy Gradients]]` - broken: 35 + mention: 5 = 40

**Diversity filter**: All same type (broken links) → OK in this case (geen andere types beschikbaar)

**Learning values** (infer from context):
1. Context: "fundamental for value estimation" → "begrijp hoe de Bellman Equation value estimation definieert"
2. Context: "Common algorithms include" → "begrijp hoe Q-Learning werkt als RL algoritme"
3. Context: "Common algorithms include" → "begrijp hoe Policy Gradients werken als RL algoritme"

**Output**:
```markdown
### Verken verder
1. [[Bellman Equation]] - begrijp hoe de Bellman Equation value estimation definieert
2. [[Q-Learning]] - begrijp hoe Q-Learning werkt als RL algoritme
3. [[Policy Gradients]] - begrijp hoe Policy Gradients werken als RL algoritme
```

## Example 3: Fallback with Reasoning Mode

**Input note**: `gradient-descent.md`

**Note content**:
```markdown
---
title: Gradient Descent
tags: AI/optimization
---

Gradient descent optimizes functions by following the negative gradient.
Step size is controlled by learning rate.
```

**Discovery process**:

1. **Extract links**: none
2. **Broken links**: none
3. **Semantic gaps**: "negative gradient", "learning rate" → check if exist as links
   - Neither exists as separate notes
   - Create candidates but low mention count
4. **Primary candidates**: 0 → TRIGGER FALLBACK

**Fallback - Distance-2**: No distance-1 notes to explore

**Fallback - Domain matching**:
- Scan vault for `tags: AI/optimization`
- Found: `adam-optimizer.md` (stub), `momentum.md` (stub)
- Add as kandidaten (score: 10 each)

**Fallback - Reasoning mode** (random selected: Extensions):
- "Na gradient descent komt logisch..."
- Generate: "Stochastic Gradient Descent", "Adaptive Learning Rates"
- Add as kandidaten (score: 5 each)

**Candidates**: 4 total

**Scoring**:
1. `[[Adam Optimizer]]` - domain: 10 + stub_quality: 15 = 25
2. `[[Momentum]]` - domain: 10 + stub_quality: 15 = 25
3. `[[Stochastic Gradient Descent]]` - reasoning: 5 = 5
4. `[[Adaptive Learning Rates]]` - reasoning: 5 = 5

**Top 3**: Adam, Momentum, SGD

**Learning values**:
1. Read adam stub → "begrijp hoe Adam adaptive learning rates combineert met momentum"
2. Read momentum stub → "begrijp hoe momentum gradient descent versnelt"
3. Reasoning context → "begrijp hoe Stochastic Gradient Descent efficiency verbetert met mini-batches"

**Output**:
```markdown
### Verken verder
1. [[Adam Optimizer]] - begrijp hoe Adam adaptive learning rates combineert met momentum
2. [[Momentum]] - begrijp hoe momentum gradient descent versnelt
3. [[Stochastic Gradient Descent]] - begrijp hoe Stochastic Gradient Descent efficiency verbetert met mini-batches
```

## Example 4: Ultimate Fallback (No Candidates Found)

**Input note**: `meditation-techniques.md` (obscure topic, geen AI/tech tags)

**Note content**:
```markdown
---
title: Meditation Techniques
tags: personal/practice
---

Various breathing exercises for focus and calm.
```

**Discovery process**:

1. **Primary discovery**: No links, no gaps → 0 candidates
2. **Fallback - Distance-2**: No distance-1 to explore
3. **Fallback - Domain**: No other notes with `personal/practice`
4. **Fallback - Reasoning**: Generates generic suggestions but very weak (score: 5)
5. **Total candidates**: <3 → ULTIMATE FALLBACK

**Ultimate fallback logic**:
- Analyze topic: "Meditation Techniques"
- Generate 3 generieke richtingen:
  1. Related domain: "Mindfulness" (related practice)
  2. Practical application: "Daily Meditation Practice" (how to apply)
  3. Historical context: "Buddhist Meditation Origins" (historical development)

**Learning values** (generic but topic-specific):
1. "begrijp hoe Mindfulness zich verhoudt tot meditatie technieken"
2. "begrijp hoe je een dagelijkse meditatie praktijk opbouwt"
3. "begrijp hoe meditatie technieken zich ontwikkeld hebben vanuit het Boeddhisme"

**Output**:
```markdown
### Verken verder
Dit topic lijkt geïsoleerd in je vault. Hier zijn drie richtingen om het netwerk uit te breiden:
1. [[Mindfulness]] - begrijp hoe Mindfulness zich verhoudt tot meditatie technieken
2. [[Daily Meditation Practice]] - begrijp hoe je een dagelijkse meditatie praktijk opbouwt
3. [[Buddhist Meditation Origins]] - begrijp hoe meditatie technieken zich ontwikkeld hebben vanuit het Boeddhisme
```
