from rdflib import Namespace, RDF, RDFS, XSD

# Определяем пространства имен
CG = Namespace("http://competencygraph.org/ontology#")
SCHEMA = Namespace("http://schema.org/")

# Классы
class Classes:
    """Основные классы онтологии"""
    Competency = CG.Competency
    CompetencyVersion = CG.CompetencyVersion
    ConflictRecord = CG.ConflictRecord

# Свойства
class Properties:
    """Свойства для описания компетенций и связей"""
    # Основные свойства компетенции
    name = SCHEMA.name
    description = SCHEMA.description
    level = CG.level
    created = SCHEMA.dateCreated
    modified = SCHEMA.dateModified

    # Свойства версионирования
    version = CG.version
    previousVersion = CG.previousVersion
    changes = CG.changes
    author = SCHEMA.author

    # Свойства связей
    hasChild = CG.hasChild
    hasParent = CG.hasParent
    weight = CG.weight

    # Свойства конфликтов
    hasConflict = CG.hasConflict
    conflictType = CG.conflictType
    conflictingFields = CG.conflictingFields
    resolvedBy = CG.resolvedBy
    resolutionTime = CG.resolutionTime

# SPARQL-шаблоны для часто используемых запросов
SPARQL_TEMPLATES = {
    "get_competency": """
        SELECT ?name ?description ?level ?version
        WHERE {{
            {uri} a cg:Competency ;
                  schema:name ?name ;
                  schema:description ?description ;
                  cg:level ?level ;
                  cg:version ?version .
        }}
    """,

    "get_children": """
        SELECT ?child ?name ?level
        WHERE {{
            {uri} cg:hasChild ?child .
            ?child schema:name ?name ;
                   cg:level ?level .
        }}
    """,

    "get_versions": """
        SELECT ?version ?changes ?author ?timestamp
        WHERE {{
            {uri} cg:version ?version ;
                  cg:changes ?changes ;
                  schema:author ?author ;
                  schema:dateModified ?timestamp .
        }}
        ORDER BY DESC(?version)
    """,

    "check_conflicts": """
        SELECT ?conflict ?type ?fields
        WHERE {{
            {uri} cg:hasConflict ?conflict .
            ?conflict cg:conflictType ?type ;
                     cg:conflictingFields ?fields .
        }}
    """
}
