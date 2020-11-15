match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[r:input|output]->(b),
    (b:PhysicalEntity)
where '$species' = s.displayName
and b.stId =~ ('R-(' + s.abbreviation + '|ALL|NUL)-.*')
return 
    { data: a, labels: labels(a) } as source, 
    { type: type(r), data: r} as relationship, 
    { data: b, labels: labels(b) } as target

union

// Non-native reactome relationships
match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:catalystActivity]->()-[:physicalEntity]->(b),
    (b:PhysicalEntity)
where '$species' = s.displayName
and b.stId =~ ('R-(' + s.abbreviation + '|ALL|NUL)-.*')
return 
    { data: a, labels: labels(a) } as source, 
    { type: 'catalyst', data: {order: null, stoichiometry: 0}} as relationship, 
    { data: b, labels: labels(b) } as target

union


match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:regulatedBy]->(:PositiveRegulation)-[:regulator]->(b),
    (b:PhysicalEntity)
where '$species' = s.displayName
and b.stId =~ ('R-(' + s.abbreviation + '|ALL|NUL)-.*')
return 
    { data: a, labels: labels(a) } as source, 
    { type: 'positiveRegulator', data: {order: null, stoichiometry: 0}} as relationship, 
    { data: b, labels: labels(b) } as target

union

match 
    (a:Event),
    (a)-[:species]->(s:Species),
    (a)-[:regulatedBy]->(:NegativeRegulation)-[:regulator]->(b),
    (b:PhysicalEntity)
where '$species' = s.displayName
and b.stId =~ ('R-(' + s.abbreviation + '|ALL|NUL)-.*')
return 
    { data: a, labels: labels(a) } as source, 
    { type: 'negativeRegulator', data: {order: null, stoichiometry: 0}} as relationship, 
    { data: b, labels: labels(b) } as target;