# Discovery Engine Validation

Manual validation tests om te verifiëren dat de discovery engine correct werkt.

## Test Setup

Gebruik een test vault met bekende structuur:
- Notes met stubs
- Notes met broken links
- Notes met weinig/geen links
- Notes in verschillende domeinen

## Validation Tests

### Test 1: Distance-1 Stub Detection

**Input**: Note met minimaal 2 `[[stub-links]]`

**Expected**:
- Beide stubs verschijnen in kandidaten
- Score = 40 voor elk
- Learning values zijn specifiek (niet "begrijp wat [topic] is")

**Pass criteria**:
- ✅ Stubs correct geïdentificeerd
- ✅ Score klopt
- ✅ Learning values beginnen met "begrijp" + vraagwoord

### Test 2: Broken Link Detection

**Input**: Note met `[[Non-existent Topic]]` link

**Expected**:
- Broken link verschijnt als kandidaat
- Score = 35
- Learning value inferred uit context (surrounding sentence)

**Pass criteria**:
- ✅ Broken link detected
- ✅ Learning value is relevant (niet generic)
- ✅ Context gebruikt voor inference

### Test 3: Fallback Trigger

**Input**: Note zonder links of met enkel non-stub links

**Expected**:
- Primary discovery yields <3
- Fallback triggered
- Distance-2 OR domain matching OR reasoning gebruikt
- Uiteindelijk 3 kandidaten geproduceerd

**Pass criteria**:
- ✅ Fallback triggered at <3
- ✅ Multiple strategies tried
- ✅ Always produces 3 suggestions

### Test 4: Diversity Filter

**Input**: Note met 5+ stubs (all distance-1)

**Expected**:
- Top 3 scores: 5 distance-1 stubs
- Diversity filter activates
- #3 replaced met hoogste uit andere categorie (semantic/broken/reasoning)

**Pass criteria**:
- ✅ Top 3 not all same type
- ✅ At least 2 different types in output
- ✅ Replacement logged/traceable

### Test 5: Circular Reference Handling

**Input**: Vault met A→B→A cycle, start from A

**Expected**:
- Distance-2 exploration doesn't loop infinitely
- A not suggested as candidate when starting from A
- Process completes <5s

**Pass criteria**:
- ✅ No infinite loop
- ✅ No duplicate candidates
- ✅ Timeout not triggered

### Test 6: Timeout Protection

**Input**: Very large vault (10,000+ notes), complex topic

**Expected**:
- Discovery stops at 5s
- Returns whatever candidates found so far (can be <3)
- Graceful degradation, no crash

**Pass criteria**:
- ✅ Hard timeout at 5s
- ✅ Partial results returned
- ✅ No errors/crashes

### Test 7: Ultimate Fallback

**Input**: Isolated note (no links, unique domain, no related notes)

**Expected**:
- Primary yields 0
- Fallback yields 0
- Ultimate fallback generates 3 generic but topic-specific suggestions
- Format: "Dit topic lijkt geïsoleerd..."

**Pass criteria**:
- ✅ Generic suggestions generated
- ✅ Still topic-relevant (not completely generic)
- ✅ Always 3 suggestions

### Test 8: Output Format Consistency

**Input**: Any note (run multiple times)

**Expected**:
- Every kandidaat: `[[Topic]] - begrijp [x]`
- Learning value always starts with "begrijp" + vraagwoord
- No formatting errors (double brackets, missing dash, etc.)

**Pass criteria**:
- ✅ Consistent format across all suggestions
- ✅ Valid wikilink syntax
- ✅ Learning values well-formed

## Manual Quality Assessment

Beyond technical tests, assess quality:

**Relevance**: Zouden de suggesties interessant zijn om te verkennen?
- Score 1-5 per suggestion
- Target: average >3.5

**Diversity**: Zijn de 3 suggesties verschillend genoeg?
- Same topic different aspects: OK
- Identical concepts: NOT OK

**Learning values**: Zijn ze actionable en specifiek?
- Good: "begrijp hoe multi-head attention parallel operations combineert"
- Bad: "begrijp wat multi-head attention is"

## Success Criteria

All 8 tests pass + quality assessment >3.5 = validation complete.
