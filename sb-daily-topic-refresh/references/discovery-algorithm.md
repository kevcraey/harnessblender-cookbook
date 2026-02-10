# Discovery Algorithm - Technical Pseudocode

Complete technical specification for the discovery engine in Python-style pseudocode format.

## 1. Main Discovery Function

```python
def discover_related_topics(note_path: str, vault_path: str, max_duration: int = 5000) -> List[Candidate]:
    """
    Main entry point for discovery engine.

    Args:
        note_path: Path to the current note being refreshed
        vault_path: Root path of the Obsidian vault
        max_duration: Maximum execution time in milliseconds (default: 5000)

    Returns:
        List of 3 Candidate objects with topic, score, learning_value
    """
    start_time = current_time_ms()
    candidates = []
    visited_notes = set()

    # Load note content and metadata
    note = parse_note(note_path)
    visited_notes.add(note_path)

    # Phase 1: Primary Discovery (fast, direct)
    try:
        primary_candidates = run_primary_discovery(note, vault_path, visited_notes)
        candidates.extend(primary_candidates)

        # Check timeout
        if current_time_ms() - start_time > max_duration:
            log_warning(f"Discovery timeout after primary phase, found {len(candidates)} candidates")
            return select_top_candidates(candidates, note)
    except Exception as e:
        log_error(f"Primary discovery failed: {e}")

    # Phase 2: Fallback Discovery (only if <3 candidates)
    if len(candidates) < 3:
        try:
            fallback_candidates = run_fallback_discovery(
                note,
                vault_path,
                visited_notes,
                remaining_time=max_duration - (current_time_ms() - start_time)
            )
            candidates.extend(fallback_candidates)

            # Check timeout
            if current_time_ms() - start_time > max_duration:
                log_warning(f"Discovery timeout after fallback phase, found {len(candidates)} candidates")
                return select_top_candidates(candidates, note)
        except Exception as e:
            log_error(f"Fallback discovery failed: {e}")

    # Ultimate fallback: ensure we always have 3 suggestions
    if len(candidates) < 3:
        generic_candidates = generate_generic_fallbacks(note, 3 - len(candidates))
        candidates.extend(generic_candidates)

    # Select and return top 3 with diversity
    top_3 = select_top_candidates(candidates, note)

    # Generate learning values
    for candidate in top_3:
        if not candidate.learning_value:
            candidate.learning_value = generate_learning_value(candidate, note, vault_path)

    return top_3
```

## 2. Primary Discovery Functions

### 2.1 Primary Discovery Orchestrator

```python
def run_primary_discovery(note: Note, vault_path: str, visited_notes: Set[str]) -> List[Candidate]:
    """
    Execute all primary discovery strategies.

    Strategies:
    1. Distance-1 graph scan (wikilinks + related-to)
    2. Broken link detection
    3. Stub detection
    4. Semantic gap analysis

    Returns:
        List of candidates found via primary methods
    """
    candidates = []

    # Strategy 1: Distance-1 Graph Scan
    distance_1_candidates = scan_distance_1_graph(note, vault_path, visited_notes)
    candidates.extend(distance_1_candidates)

    # Strategy 2: Broken Links (high-value candidates)
    broken_link_candidates = detect_broken_links(note, vault_path)
    candidates.extend(broken_link_candidates)

    # Strategy 3: Semantic Gaps
    semantic_gap_candidates = analyze_semantic_gaps(note, vault_path)
    candidates.extend(semantic_gap_candidates)

    return candidates
```

### 2.2 Distance-1 Graph Scan

```python
def scan_distance_1_graph(note: Note, vault_path: str, visited_notes: Set[str]) -> List[Candidate]:
    """
    Scan immediate connections from wikilinks and related-to frontmatter.

    Returns candidates that are:
    - Stubs (exist but <100 words)
    - Broken links (mentioned but don't exist)
    """
    candidates = []
    seen_topics = set()

    # Extract wikilinks from note body
    wikilinks = extract_wikilinks(note.content)

    # Extract related-to from frontmatter
    if note.frontmatter and 'related-to' in note.frontmatter:
        related_topics = note.frontmatter['related-to']
        if isinstance(related_topics, str):
            related_topics = [related_topics]
        wikilinks.extend(related_topics)

    # Process each link
    for link in wikilinks:
        # Clean link (remove aliases, anchors)
        topic = clean_wikilink(link)

        # Skip if already processed
        if topic in seen_topics:
            continue
        seen_topics.add(topic)

        # Resolve path
        topic_path = resolve_note_path(topic, vault_path)

        # Check if exists
        if not file_exists(topic_path):
            # Broken link - high value candidate
            candidate = Candidate(
                topic=topic,
                source="broken_link",
                distance=1,
                base_score=35,
                context=extract_link_context(note.content, topic)
            )
            candidates.append(candidate)
            continue

        # Check if stub
        if is_stub(topic_path):
            candidate = Candidate(
                topic=topic,
                source="distance_1_stub",
                distance=1,
                base_score=40,
                stub_path=topic_path
            )
            candidates.append(candidate)
            visited_notes.add(topic_path)

    return candidates
```

### 2.3 Broken Link Detection

```python
def detect_broken_links(note: Note, vault_path: str) -> List[Candidate]:
    """
    Find all [[wikilinks]] that point to non-existent notes.
    These are high-value candidates (score: 35).
    """
    candidates = []

    # Regex to extract all [[wikilinks]]
    pattern = r'\[\[([^\]]+)\]\]'
    matches = re.finditer(pattern, note.content)

    for match in matches:
        raw_link = match.group(1)

        # Handle pipe syntax: [[target|display]]
        if '|' in raw_link:
            topic = raw_link.split('|')[0].strip()
        # Handle section links: [[note#section]]
        elif '#' in raw_link:
            topic = raw_link.split('#')[0].strip()
        else:
            topic = raw_link.strip()

        # Skip empty links
        if not topic:
            continue

        # Check if note exists
        topic_path = resolve_note_path(topic, vault_path)

        if not file_exists(topic_path):
            # Extract surrounding context (sentence containing the link)
            context = extract_sentence_context(note.content, match.start())

            candidate = Candidate(
                topic=topic,
                source="broken_link",
                distance=1,
                base_score=35,
                context=context,
                mention_count=count_mentions(note.content, topic)
            )
            candidates.append(candidate)

    return candidates
```

### 2.4 Semantic Gap Analysis

```python
def analyze_semantic_gaps(note: Note, vault_path: str) -> List[Candidate]:
    """
    Find key terms that are mentioned but not linked.
    These represent implicit knowledge gaps.
    """
    candidates = []

    # Extract key terms from content
    key_terms = extract_key_terms(note.content)

    # Get all existing wikilinks to filter out
    existing_links = set(extract_wikilinks(note.content))

    for term in key_terms:
        # Skip if already linked
        if term in existing_links:
            continue

        # Skip if note exists and is not a stub
        term_path = resolve_note_path(term, vault_path)
        if file_exists(term_path) and not is_stub(term_path):
            continue

        # This is a semantic gap
        candidate = Candidate(
            topic=term,
            source="semantic_gap",
            distance=1,
            base_score=30,
            mention_count=count_mentions(note.content, term),
            context=extract_first_mention_context(note.content, term)
        )
        candidates.append(candidate)

    return candidates


def extract_key_terms(content: str) -> List[str]:
    """
    Extract potential key terms from note content.

    Heuristics:
    - Capitalized words/phrases (CamelCase, Title Case)
    - Technical abbreviations (AI, ML, NLP)
    - Words in backticks or bold
    - Domain-specific patterns
    """
    key_terms = []

    # Pattern 1: CamelCase words
    camel_case_pattern = r'\b([A-Z][a-z]+[A-Z][a-z]+[A-Za-z]*)\b'
    key_terms.extend(re.findall(camel_case_pattern, content))

    # Pattern 2: Multiple capitalized words (excluding sentence starts)
    title_case_pattern = r'(?<!\.)\s([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)'
    key_terms.extend(re.findall(title_case_pattern, content))

    # Pattern 3: Abbreviations (2-5 uppercase letters)
    abbreviation_pattern = r'\b([A-Z]{2,5})\b'
    key_terms.extend(re.findall(abbreviation_pattern, content))

    # Pattern 4: Words in backticks
    backtick_pattern = r'`([^`]+)`'
    key_terms.extend(re.findall(backtick_pattern, content))

    # Pattern 5: Bold text (potential emphasis)
    bold_pattern = r'\*\*([^\*]+)\*\*'
    key_terms.extend(re.findall(bold_pattern, content))

    # Deduplicate and clean
    key_terms = list(set([term.strip() for term in key_terms if len(term.strip()) > 2]))

    return key_terms
```

## 3. Fallback Discovery Functions

### 3.1 Fallback Discovery Orchestrator

```python
def run_fallback_discovery(
    note: Note,
    vault_path: str,
    visited_notes: Set[str],
    remaining_time: int
) -> List[Candidate]:
    """
    Execute fallback strategies when primary discovery yields <3 candidates.

    Strategies:
    1. Distance-2 exploration
    2. Domain matching (shared tags/categories)
    3. Reasoning modes (prerequisites OR extensions)

    Returns:
        List of candidates found via fallback methods
    """
    candidates = []
    start_time = current_time_ms()

    # Strategy 1: Distance-2 Exploration
    if current_time_ms() - start_time < remaining_time:
        try:
            distance_2_candidates = explore_distance_2(note, vault_path, visited_notes)
            candidates.extend(distance_2_candidates)
        except Exception as e:
            log_error(f"Distance-2 exploration failed: {e}")

    # Strategy 2: Domain Matching
    if current_time_ms() - start_time < remaining_time:
        try:
            domain_candidates = match_by_domain(note, vault_path)
            candidates.extend(domain_candidates)
        except Exception as e:
            log_error(f"Domain matching failed: {e}")

    # Strategy 3: Reasoning Modes (random selection for variety)
    if current_time_ms() - start_time < remaining_time:
        try:
            mode = random.choice(['prerequisites', 'extensions'])
            reasoning_candidates = apply_reasoning_mode(note, mode)
            candidates.extend(reasoning_candidates)
        except Exception as e:
            log_error(f"Reasoning mode failed: {e}")

    return candidates
```

### 3.2 Distance-2 Exploration

```python
def explore_distance_2(note: Note, vault_path: str, visited_notes: Set[str]) -> List[Candidate]:
    """
    Follow links from distance-1 notes to find distance-2 candidates.

    Protection against circular references via visited_notes tracking.
    """
    candidates = []

    # Get all distance-1 links
    distance_1_links = extract_wikilinks(note.content)
    if note.frontmatter and 'related-to' in note.frontmatter:
        related = note.frontmatter['related-to']
        if isinstance(related, str):
            related = [related]
        distance_1_links.extend(related)

    # Explore each distance-1 note
    for d1_link in distance_1_links:
        d1_topic = clean_wikilink(d1_link)
        d1_path = resolve_note_path(d1_topic, vault_path)

        # Skip if doesn't exist or already visited
        if not file_exists(d1_path) or d1_path in visited_notes:
            continue

        visited_notes.add(d1_path)

        # Parse distance-1 note
        d1_note = parse_note(d1_path)

        # Extract its links
        d2_links = extract_wikilinks(d1_note.content)
        if d1_note.frontmatter and 'related-to' in d1_note.frontmatter:
            related = d1_note.frontmatter['related-to']
            if isinstance(related, str):
                related = [related]
            d2_links.extend(related)

        # Process each distance-2 link
        for d2_link in d2_links:
            d2_topic = clean_wikilink(d2_link)
            d2_path = resolve_note_path(d2_topic, vault_path)

            # Skip if already visited (circular reference protection)
            if d2_path in visited_notes:
                continue

            # Check if broken or stub
            if not file_exists(d2_path):
                candidate = Candidate(
                    topic=d2_topic,
                    source="distance_2_broken",
                    distance=2,
                    base_score=20,
                    via=d1_topic
                )
                candidates.append(candidate)
            elif is_stub(d2_path):
                candidate = Candidate(
                    topic=d2_topic,
                    source="distance_2_stub",
                    distance=2,
                    base_score=20,
                    stub_path=d2_path,
                    via=d1_topic
                )
                candidates.append(candidate)
                visited_notes.add(d2_path)

    return candidates
```

### 3.3 Domain Matching

```python
def match_by_domain(note: Note, vault_path: str) -> List[Candidate]:
    """
    Find candidates with overlapping tags/categories.
    Useful when note lacks explicit links.
    """
    candidates = []

    # Extract tags from current note
    note_tags = extract_tags(note)

    if not note_tags:
        return candidates

    # Scan vault for notes with overlapping tags
    vault_index = load_vault_index(vault_path)  # Cached structure

    for other_path, other_tags in vault_index.items():
        # Skip current note
        if other_path == note.path:
            continue

        # Calculate tag overlap
        overlap = set(note_tags).intersection(set(other_tags))

        if overlap:
            # Check if stub
            if is_stub(other_path):
                topic = extract_topic_name(other_path)
                candidate = Candidate(
                    topic=topic,
                    source="domain_match",
                    distance=None,
                    base_score=10,
                    stub_path=other_path,
                    shared_tags=list(overlap)
                )
                candidates.append(candidate)

    return candidates


def extract_tags(note: Note) -> List[str]:
    """
    Extract all tags from frontmatter and inline tags.
    """
    tags = []

    # Frontmatter tags
    if note.frontmatter and 'tags' in note.frontmatter:
        fm_tags = note.frontmatter['tags']
        if isinstance(fm_tags, str):
            tags.append(fm_tags)
        elif isinstance(fm_tags, list):
            tags.extend(fm_tags)

    # Inline tags (#tag format)
    inline_pattern = r'#([a-zA-Z0-9_/-]+)'
    inline_tags = re.findall(inline_pattern, note.content)
    tags.extend(inline_tags)

    return list(set(tags))
```

### 3.4 Reasoning Modes

```python
def apply_reasoning_mode(note: Note, mode: str) -> List[Candidate]:
    """
    Use reasoning to infer missing topics.

    Modes:
    - prerequisites: topics you should know BEFORE current topic
    - extensions: topics that build ON current topic

    Returns 2-3 inferred candidates with low base score (5).
    """
    candidates = []
    topic_name = note.title or extract_topic_name(note.path)

    if mode == 'prerequisites':
        # Infer prerequisites based on topic domain
        prerequisites = infer_prerequisites(topic_name, note.content)
        for prereq in prerequisites:
            candidate = Candidate(
                topic=prereq,
                source="reasoning_prerequisite",
                distance=None,
                base_score=5,
                reasoning=f"Understanding {prereq} is foundational for {topic_name}"
            )
            candidates.append(candidate)

    elif mode == 'extensions':
        # Infer logical next steps
        extensions = infer_extensions(topic_name, note.content)
        for ext in extensions:
            candidate = Candidate(
                topic=ext,
                source="reasoning_extension",
                distance=None,
                base_score=5,
                reasoning=f"{ext} builds upon concepts from {topic_name}"
            )
            candidates.append(candidate)

    return candidates


def infer_prerequisites(topic: str, content: str) -> List[str]:
    """
    Simple heuristic-based prerequisite inference.

    Look for:
    - "requires understanding of..."
    - "builds on..."
    - "assumes knowledge of..."
    - Domain-specific patterns
    """
    prerequisites = []

    # Pattern 1: Explicit requirements
    requirement_pattern = r'(?:requires?|assumes?|builds? on|needs?)\s+(?:understanding of\s+)?([A-Z][a-zA-Z\s]+)'
    matches = re.findall(requirement_pattern, content, re.IGNORECASE)
    prerequisites.extend([m.strip() for m in matches])

    # Pattern 2: Domain-specific inference
    if 'neural' in topic.lower() or 'deep learning' in topic.lower():
        prerequisites.extend(['Linear Algebra', 'Calculus', 'Probability Theory'])
    elif 'algorithm' in topic.lower():
        prerequisites.extend(['Data Structures', 'Complexity Analysis'])
    elif 'quantum' in topic.lower():
        prerequisites.extend(['Linear Algebra', 'Classical Mechanics', 'Wave Functions'])

    # Limit to 2-3 most relevant
    return prerequisites[:3]


def infer_extensions(topic: str, content: str) -> List[str]:
    """
    Simple heuristic-based extension inference.

    Look for:
    - Advanced variations
    - Practical applications
    - Related subfields
    """
    extensions = []

    # Pattern 1: Explicit forward references
    extension_pattern = r'(?:leads to|enables|advanced|next step)\s+([A-Z][a-zA-Z\s]+)'
    matches = re.findall(extension_pattern, content, re.IGNORECASE)
    extensions.extend([m.strip() for m in matches])

    # Pattern 2: Domain-specific inference
    if 'theory' in topic.lower():
        extensions.append(f'{topic} in Practice')
        extensions.append(f'Applications of {topic}')
    elif 'basic' in topic.lower() or 'introduction' in topic.lower():
        extensions.append(f'Advanced {topic.replace("Basic", "").replace("Introduction to", "")}')

    # Limit to 2-3 most relevant
    return extensions[:3]
```

## 4. Scoring Functions

### 4.1 Candidate Scoring

```python
def calculate_candidate_score(candidate: Candidate, note: Note, vault_path: str) -> int:
    """
    Calculate total score (0-100) for a candidate.

    Components:
    - Distance weight (40 max): based on source type
    - Mention count (20 max): how often mentioned
    - Stub quality (20 max): has stub vs inference
    - Recency bias (10 max): related to recent stages
    - Freshness (10 max): not recently suggested
    """
    score = 0

    # Component 1: Distance weight (40 max)
    distance_scores = {
        'distance_1_stub': 40,
        'broken_link': 35,
        'semantic_gap': 30,
        'distance_2_stub': 20,
        'distance_2_broken': 20,
        'domain_match': 10,
        'reasoning_prerequisite': 5,
        'reasoning_extension': 5
    }
    score += distance_scores.get(candidate.source, 0)

    # Component 2: Mention count (20 max)
    if candidate.mention_count:
        # Linear scale: 1 mention = 5 points, 4+ mentions = 20 points
        mention_score = min(candidate.mention_count * 5, 20)
        score += mention_score

    # Component 3: Stub quality (20 max)
    if candidate.stub_path:
        # Has actual stub note
        score += 15
    elif candidate.source == 'broken_link':
        # Explicitly mentioned but missing
        score += 10
    else:
        # Pure inference
        score += 5

    # Component 4: Recency bias (10 max)
    recency_score = calculate_recency_score(candidate, vault_path)
    score += recency_score

    # Component 5: Freshness (10 max)
    freshness_score = calculate_freshness_score(candidate, vault_path)
    score += freshness_score

    return min(score, 100)


def calculate_recency_score(candidate: Candidate, vault_path: str) -> int:
    """
    Check if candidate relates to recently staged items.

    Returns:
        10 if related to items staged in last 7 days, 0 otherwise
    """
    # Load staging history
    staging_history = load_staging_history(vault_path)

    # Get items staged in last 7 days
    recent_items = [
        item for item in staging_history
        if days_since(item.timestamp) <= 7
    ]

    if not recent_items:
        return 0

    # Extract tags from recent items
    recent_tags = set()
    for item in recent_items:
        if item.tags:
            recent_tags.update(item.tags)

    # Check if candidate shares tags
    if candidate.shared_tags:
        overlap = set(candidate.shared_tags).intersection(recent_tags)
        if overlap:
            return 10

    return 0


def calculate_freshness_score(candidate: Candidate, vault_path: str) -> int:
    """
    Check if candidate was recently suggested.

    Returns:
        10 if NOT suggested in last 30 days, 0 otherwise
    """
    # Load discovery history
    history_file = os.path.join(vault_path, '.discovery-history.json')

    if not file_exists(history_file):
        return 10  # Never suggested before

    history = json.load(open(history_file))

    # Check if candidate in recent suggestions
    for entry in history:
        if entry['topic'] == candidate.topic:
            days_ago = days_since(entry['timestamp'])
            if days_ago < 30:
                return 0  # Recently suggested

    return 10  # Not recently suggested
```

### 4.2 Top Candidate Selection

```python
def select_top_candidates(candidates: List[Candidate], note: Note) -> List[Candidate]:
    """
    Select top 3 candidates with diversity filter.

    Process:
    1. Calculate scores for all candidates
    2. Sort by score (descending)
    3. Select top 3
    4. Apply diversity filter to ensure variety

    Returns:
        List of exactly 3 candidates
    """
    if not candidates:
        return []

    # Calculate scores
    vault_path = extract_vault_path(note.path)
    for candidate in candidates:
        candidate.score = calculate_candidate_score(candidate, note, vault_path)

    # Sort by score
    candidates.sort(key=lambda c: c.score, reverse=True)

    # Select top 3
    if len(candidates) <= 3:
        return candidates

    top_3 = candidates[:3]

    # Apply diversity filter
    top_3 = apply_diversity_filter(top_3, candidates[3:])

    return top_3


def apply_diversity_filter(top_3: List[Candidate], remaining: List[Candidate]) -> List[Candidate]:
    """
    Ensure variety in top 3 by replacing #3 if all are same category.

    Categories:
    - distance_1 (stub, broken, semantic)
    - distance_2
    - domain_match
    - reasoning
    """
    if len(top_3) < 3 or not remaining:
        return top_3

    # Categorize top 3
    categories = [categorize_candidate(c) for c in top_3]

    # Check if all same category
    if len(set(categories)) == 1:
        # Find best candidate from different category
        for candidate in remaining:
            if categorize_candidate(candidate) != categories[0]:
                # Replace #3 with more diverse option
                top_3[2] = candidate
                break

    return top_3


def categorize_candidate(candidate: Candidate) -> str:
    """
    Categorize candidate by source type.
    """
    if candidate.source in ['distance_1_stub', 'broken_link', 'semantic_gap']:
        return 'distance_1'
    elif candidate.source in ['distance_2_stub', 'distance_2_broken']:
        return 'distance_2'
    elif candidate.source == 'domain_match':
        return 'domain_match'
    elif candidate.source in ['reasoning_prerequisite', 'reasoning_extension']:
        return 'reasoning'
    else:
        return 'other'
```

## 5. Learning Value Generation

```python
def generate_learning_value(candidate: Candidate, note: Note, vault_path: str) -> str:
    """
    Generate "begrijp [x]" text for candidate.

    Strategy depends on candidate source:
    - Stub: read metadata and infer value
    - Broken link: use context where link appears
    - Reasoning: use the reasoning that created it
    - Domain match: use shared tags

    Returns:
        String starting with "begrijp hoe/wat/waarom/welke"
    """
    if candidate.learning_value:
        return candidate.learning_value

    # Strategy 1: Stub note exists
    if candidate.stub_path:
        return generate_value_from_stub(candidate.stub_path, candidate.topic)

    # Strategy 2: Broken link with context
    if candidate.source == 'broken_link' and candidate.context:
        return generate_value_from_context(candidate.context, candidate.topic)

    # Strategy 3: Reasoning mode
    if candidate.reasoning:
        return generate_value_from_reasoning(candidate.reasoning, candidate.topic, note.title)

    # Strategy 4: Domain match
    if candidate.shared_tags:
        return generate_value_from_domain(candidate.topic, candidate.shared_tags, note.title)

    # Fallback: generic value
    return f"begrijp wat {candidate.topic} inhoudt"


def generate_value_from_stub(stub_path: str, topic: str) -> str:
    """
    Infer learning value from stub note metadata.
    """
    stub = parse_note(stub_path)

    # Check for explicit description in frontmatter
    if stub.frontmatter and 'description' in stub.frontmatter:
        desc = stub.frontmatter['description']
        return f"begrijp {desc}"

    # Infer from tags
    if stub.frontmatter and 'tags' in stub.frontmatter:
        tags = stub.frontmatter['tags']
        if isinstance(tags, str):
            tags = [tags]

        # Heuristics based on tags
        if any('concept' in t for t in tags):
            return f"begrijp wat {topic} betekent"
        elif any('algorithm' in t for t in tags):
            return f"begrijp hoe het {topic} algoritme werkt"
        elif any('theory' in t for t in tags):
            return f"begrijp de theorie achter {topic}"
        elif any('practice' in t or 'application' in t for t in tags):
            return f"begrijp hoe {topic} toegepast wordt"

    # Fallback: simple description
    return f"begrijp wat {topic} is"


def generate_value_from_context(context: str, topic: str) -> str:
    """
    Infer learning value from surrounding context.

    Example:
        Context: "The [[Bellman Equation]] is fundamental for RL"
        Output: "begrijp hoe de Bellman Equation fundamenteel is voor RL"
    """
    # Look for key relationship words
    if 'fundamental' in context.lower():
        domain = extract_domain_from_context(context)
        return f"begrijp hoe {topic} fundamenteel is voor {domain}"
    elif 'enables' in context.lower() or 'allows' in context.lower():
        return f"begrijp hoe {topic} nieuwe mogelijkheden biedt"
    elif 'improves' in context.lower() or 'optimizes' in context.lower():
        return f"begrijp hoe {topic} verbeteringen mogelijk maakt"
    elif 'based on' in context.lower():
        return f"begrijp waarop {topic} gebaseerd is"

    # Fallback: generic
    return f"begrijp wat {topic} inhoudt"


def generate_value_from_reasoning(reasoning: str, topic: str, current_topic: str) -> str:
    """
    Generate value from reasoning that led to candidate.
    """
    if 'prerequisite' in reasoning.lower() or 'foundational' in reasoning.lower():
        return f"begrijp wat {topic} is als basis voor {current_topic}"
    elif 'extension' in reasoning.lower() or 'builds upon' in reasoning.lower():
        return f"begrijp hoe {topic} voortbouwt op {current_topic}"
    else:
        return f"begrijp de relatie tussen {topic} en {current_topic}"


def generate_value_from_domain(topic: str, shared_tags: List[str], current_topic: str) -> str:
    """
    Generate value based on shared domain/tags.
    """
    if shared_tags:
        domain = shared_tags[0].split('/')[-1]  # Get last part of tag hierarchy
        return f"begrijp hoe {topic} past binnen {domain}"
    else:
        return f"begrijp wat {topic} betekent in deze context"
```

## 6. Ultimate Fallback Function

```python
def generate_generic_fallbacks(note: Note, count: int) -> List[Candidate]:
    """
    Generate generic but valuable fallback suggestions when no candidates found.

    Three directions:
    1. Related domain (broaden to adjacent field)
    2. Practical application (theory to implementation)
    3. Historical context (evolution of concept)

    Returns:
        List of generic candidates with inferred topics
    """
    fallbacks = []
    topic_name = note.title or extract_topic_name(note.path)

    # Fallback 1: Related domain
    if count >= 1:
        related_domain = infer_related_domain(topic_name)
        candidate = Candidate(
            topic=related_domain,
            source="generic_fallback_domain",
            distance=None,
            base_score=3,
            learning_value=f"begrijp hoe {related_domain} aansluit bij {topic_name}"
        )
        fallbacks.append(candidate)

    # Fallback 2: Practical application
    if count >= 2:
        application = infer_practical_application(topic_name)
        candidate = Candidate(
            topic=application,
            source="generic_fallback_practice",
            distance=None,
            base_score=2,
            learning_value=f"begrijp hoe {topic_name} in de praktijk toegepast wordt"
        )
        fallbacks.append(candidate)

    # Fallback 3: Historical context
    if count >= 3:
        historical = infer_historical_context(topic_name)
        candidate = Candidate(
            topic=historical,
            source="generic_fallback_history",
            distance=None,
            base_score=1,
            learning_value=f"begrijp de ontwikkeling van {topic_name}"
        )
        fallbacks.append(candidate)

    return fallbacks[:count]


def infer_related_domain(topic: str) -> str:
    """
    Infer adjacent domain based on topic.
    """
    # Domain mapping heuristics
    domain_map = {
        'ai': 'Cognitive Science',
        'machine learning': 'Statistics',
        'deep learning': 'Neuroscience',
        'algorithm': 'Mathematics',
        'quantum': 'Classical Physics',
        'programming': 'Computer Architecture',
        'database': 'Distributed Systems',
        'security': 'Cryptography'
    }

    topic_lower = topic.lower()
    for key, related in domain_map.items():
        if key in topic_lower:
            return related

    # Generic fallback
    return f"Aanpalend vakgebied van {topic}"


def infer_practical_application(topic: str) -> str:
    """
    Infer practical application form.
    """
    # If topic mentions theory/concept, suggest implementation
    if 'theory' in topic.lower() or 'concept' in topic.lower():
        base = topic.replace('Theory', '').replace('Concept', '').strip()
        return f"{base} Implementation"

    # If topic is technical, suggest real-world use
    if any(term in topic.lower() for term in ['algorithm', 'model', 'system']):
        return f"Real-world Applications of {topic}"

    # Generic fallback
    return f"Praktische toepassing van {topic}"


def infer_historical_context(topic: str) -> str:
    """
    Infer historical/evolution context.
    """
    return f"History and Evolution of {topic}"
```

## 7. Helper Functions

```python
# File Operations
def parse_note(note_path: str) -> Note:
    """Parse markdown note with frontmatter and content."""
    pass

def file_exists(path: str) -> bool:
    """Check if file exists."""
    pass

def is_stub(note_path: str) -> bool:
    """
    Check if note is a stub.
    Criteria: word_count < 100 OR tag:status/stub OR frontmatter.stub: true
    """
    pass

def resolve_note_path(topic: str, vault_path: str) -> str:
    """Resolve topic name to full file path."""
    pass

# Link Processing
def extract_wikilinks(content: str) -> List[str]:
    """Extract all [[wikilinks]] from content."""
    pass

def clean_wikilink(link: str) -> str:
    """Remove aliases, anchors, and clean link text."""
    pass

def extract_link_context(content: str, topic: str) -> str:
    """Extract sentence containing the topic mention."""
    pass

def extract_sentence_context(content: str, position: int) -> str:
    """Extract sentence at given character position."""
    pass

def count_mentions(content: str, term: str) -> int:
    """Count how many times term appears in content."""
    pass

# Timing
def current_time_ms() -> int:
    """Get current time in milliseconds."""
    pass

def days_since(timestamp: int) -> int:
    """Calculate days since given timestamp."""
    pass

# Vault Operations
def load_vault_index(vault_path: str) -> Dict[str, List[str]]:
    """Load cached vault structure with tags per file."""
    pass

def load_staging_history(vault_path: str) -> List[StagedItem]:
    """Load recent staging history."""
    pass

def extract_vault_path(note_path: str) -> str:
    """Extract vault root path from note path."""
    pass

def extract_topic_name(path: str) -> str:
    """Extract topic name from file path."""
    pass

# Logging
def log_warning(message: str):
    """Log warning message."""
    pass

def log_error(message: str):
    """Log error message."""
    pass

# Data Structures
class Note:
    def __init__(self):
        self.path: str = ""
        self.title: str = ""
        self.content: str = ""
        self.frontmatter: Dict = {}

class Candidate:
    def __init__(self, **kwargs):
        self.topic: str = kwargs.get('topic')
        self.source: str = kwargs.get('source')
        self.distance: Optional[int] = kwargs.get('distance')
        self.base_score: int = kwargs.get('base_score', 0)
        self.score: int = 0
        self.learning_value: str = kwargs.get('learning_value', '')
        self.stub_path: Optional[str] = kwargs.get('stub_path')
        self.context: Optional[str] = kwargs.get('context')
        self.mention_count: int = kwargs.get('mention_count', 0)
        self.shared_tags: List[str] = kwargs.get('shared_tags', [])
        self.reasoning: Optional[str] = kwargs.get('reasoning')
        self.via: Optional[str] = kwargs.get('via')  # For distance-2

class StagedItem:
    def __init__(self):
        self.path: str = ""
        self.timestamp: int = 0
        self.tags: List[str] = []
```
