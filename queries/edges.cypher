

// --- RELATIONSHIPS ---

// Native reactome relationships:
// - Entity-Entity
match 
    (a:PhysicalEntity),
    (a)-[:species]->(s:Species),
    (a)-[r:hasComponent|hasCandidate|hasMember|repeatedUnit]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, type(r) as relType, r as relData, b as target, labels(b) as targetLabels

// - Entity/Event does not exist

union 

// - Event/Entity
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[r:input|output|requiredInputComponent]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, type(r) as relType, r as relData, b as target, labels(b) as targetLabels


union 

// - Event/Event
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[r:hasEvent|precedingEvent|hasEncapsulatedEvent|reverseReaction|normalPathway|normalReaction]->(b),
    (b:Event)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, type(r) as relType, r as relData, b as target, labels(b) as targetLabels


union

// Non-native reactome relationships elaboration
// - CATALYST
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:catalystActivity]->()-[:physicalEntity]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, 'catalyst' as relType, null as relData, b as target, labels(b) as targetLabels

union

// - CATALYST_ACTIVE_UNIT
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:catalystActivity]->()-[:activeUnit]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, 'catalystActiveUnit' as relType, null as relData, b as target, labels(b) as targetLabels

union

// - POSITIVE_REGULATOR
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:regulatedBy]->(:PositiveRegulation)-[:regulator]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, 'positiveRegulator' as relType, null as relData, b as target, labels(b) as targetLabels

union

// - NEGATIVE_REGULATOR
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:regulatedBy]->(:NegativeRegulation)-[:regulator]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels, 'negativeRegulator' as relType, null as relData, b as target, labels(b) as targetLabels

union

match (a:Event),
    (a)-[:species ]->(s:Species),
    (a)-[:regulatedBy ]->()-[:activeUnit ]->(b),
    (b:PhysicalEntity)
where '$species_name' in s.name
and b.stId =~ 'R-($species_code|ALL|NUL)-.*'
return a as source, labels(a) as sourceLabels , 'regulatorActiveUnit' as relType , null as relData , b as target, labels(b) as targetLabels;