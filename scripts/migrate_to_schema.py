#!/usr/bin/env python3
"""
Migrate Canonical Ledger to Full Schema

Migrates canonical_ledger_v6.json to use the complete StorageSchema with:
- EventNodes for transactions
- EntityNodes for merchants
- AttributeFacts for scalar properties
- RelationshipFacts for connections
- Full bitemporal tracking and provenance
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from storage.schema import (
    StorageSchema,
    EventNode, EntityNode, SeriesNode,
    AttributeFact, RelationshipFact,
    EventType, EntityType, NodeType, NodeStatus,
    TemporalQualifiers, Provenance
)


def generate_statement_id(prefix: str, subject_id: str, predicate: str) -> str:
    """Generate unique statement ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}_{subject_id}_{predicate}_{timestamp}"


def create_temporal_qualifiers(transaction: Dict[str, Any]) -> TemporalQualifiers:
    """Create TemporalQualifiers from transaction data"""
    # Use transaction date as valid_from
    valid_from = transaction.get("date", datetime.now().isoformat())

    # Use provenance created_at as observed_at
    provenance_data = transaction.get("provenance", {})
    observed_at = provenance_data.get("created_at", datetime.now().isoformat())

    return TemporalQualifiers(
        valid_from=valid_from,
        valid_to=None,  # Transaction facts are generally permanent
        observed_at=observed_at,
        superseded_at=None
    )


def create_provenance(transaction: Dict[str, Any]) -> Provenance:
    """Create Provenance from transaction data"""
    provenance_data = transaction.get("provenance", {})

    observation_ids = provenance_data.get("observation_ids", [])
    source_method = provenance_data.get("source_method", "unknown")
    observer = provenance_data.get("observer", "unknown")
    created_at = provenance_data.get("created_at", datetime.now().isoformat())

    # Get confidence score
    confidence_data = transaction.get("confidence", {})
    if isinstance(confidence_data, dict):
        confidence = confidence_data.get("overall", 1.0)
    else:
        confidence = float(confidence_data) if confidence_data else 1.0

    source_document = provenance_data.get("source_document")

    return Provenance(
        observation_ids=observation_ids,
        source_method=source_method,
        observer=observer,
        created_at=created_at,
        confidence=confidence,
        source_document=source_document
    )


def migrate_transaction_to_schema(
    transaction: Dict[str, Any],
    schema: StorageSchema,
    entity_registry: Dict[str, str]  # merchant_name -> entity_id
) -> None:
    """
    Migrate a single transaction to the schema format

    Creates:
    - 1 EventNode
    - Multiple AttributeFacts (amount, description, date, currency)
    - 1 RelationshipFact (merchant)
    """
    transaction_id = transaction["id"]
    event_id = f"evt_{transaction_id}"

    # 1. Create EventNode
    event_node = EventNode(
        event_id=event_id,
        event_type=EventType.FINANCE_TRANSACTION,
        happened_at=transaction.get("date", ""),
        status=NodeStatus.VERIFIED,
        snapshot={
            "amount": transaction.get("amount"),
            "currency": transaction.get("currency", "USD"),
            "description": transaction.get("description")
        }
    )
    schema.add_event(event_node)

    # Get temporal and provenance data
    temporal = create_temporal_qualifiers(transaction)
    provenance = create_provenance(transaction)

    # 2. Create AttributeFacts for scalar properties

    # Amount fact
    if "amount" in transaction:
        amount_fact = AttributeFact(
            statement_id=generate_statement_id("attr", event_id, "amount"),
            subject_id=event_id,
            predicate="amount",
            object={
                "value": float(transaction["amount"]),
                "type": "number",
                "unit": transaction.get("currency", "USD")
            },
            temporal=temporal,
            provenance=provenance
        )
        schema.add_attribute_fact(amount_fact)

    # Description fact
    if "description" in transaction:
        description_fact = AttributeFact(
            statement_id=generate_statement_id("attr", event_id, "description"),
            subject_id=event_id,
            predicate="description",
            object={
                "value": transaction["description"],
                "type": "string"
            },
            temporal=temporal,
            provenance=provenance
        )
        schema.add_attribute_fact(description_fact)

    # Date fact
    if "date" in transaction:
        date_fact = AttributeFact(
            statement_id=generate_statement_id("attr", event_id, "date"),
            subject_id=event_id,
            predicate="date",
            object={
                "value": transaction["date"],
                "type": "date"
            },
            temporal=temporal,
            provenance=provenance
        )
        schema.add_attribute_fact(date_fact)

    # Currency fact
    if "currency" in transaction:
        currency_fact = AttributeFact(
            statement_id=generate_statement_id("attr", event_id, "currency"),
            subject_id=event_id,
            predicate="currency",
            object={
                "value": transaction["currency"],
                "type": "string"
            },
            temporal=temporal,
            provenance=provenance
        )
        schema.add_attribute_fact(currency_fact)

    # Category fact (if present)
    if "category" in transaction:
        category_fact = AttributeFact(
            statement_id=generate_statement_id("attr", event_id, "category"),
            subject_id=event_id,
            predicate="category",
            object={
                "value": transaction["category"],
                "type": "string"
            },
            temporal=temporal,
            provenance=provenance
        )
        schema.add_attribute_fact(category_fact)

    # 3. Create RelationshipFact for merchant
    if "merchant" in transaction:
        merchant_name = transaction["merchant"]

        # Get or create entity_id for merchant
        if merchant_name not in entity_registry:
            entity_id = f"ent_merchant_{len(entity_registry)}"
            entity_registry[merchant_name] = entity_id

            # Create EntityNode for merchant
            merchant_entity = EntityNode(
                entity_id=entity_id,
                type=EntityType.MERCHANT,
                status=NodeStatus.VERIFIED,
                aliases=[merchant_name]
            )
            schema.add_entity(merchant_entity)

            # Add canonical_name as AttributeFact
            canonical_name_fact = AttributeFact(
                statement_id=generate_statement_id("attr", entity_id, "canonical_name"),
                subject_id=entity_id,
                predicate="canonical_name",
                object={
                    "value": merchant_name,
                    "type": "string"
                },
                temporal=temporal,
                provenance=provenance
            )
            schema.add_attribute_fact(canonical_name_fact)

        entity_id = entity_registry[merchant_name]

        # Create RelationshipFact
        merchant_relationship = RelationshipFact(
            statement_id=generate_statement_id("rel", event_id, "merchant"),
            subject_id=event_id,
            predicate="merchant",
            target_id=entity_id,
            temporal=temporal,
            provenance=provenance
        )
        schema.add_relationship_fact(merchant_relationship)


def migrate_canonical_ledger(input_path: Path, output_path: Path) -> None:
    """
    Migrate canonical ledger to full schema format
    """
    print(f"🔄 Migrando canonical ledger...")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")
    print()

    # Load canonical ledger
    with open(input_path, 'r') as f:
        canonical_data = json.load(f)

    transactions = canonical_data.get("transactions", [])
    print(f"📊 Transacciones a migrar: {len(transactions)}")
    print()

    # Create schema
    schema = StorageSchema()
    entity_registry = {}

    # Migrate each transaction
    for i, transaction in enumerate(transactions, 1):
        if i % 500 == 0:
            print(f"  Procesando: {i}/{len(transactions)}...")

        migrate_transaction_to_schema(transaction, schema, entity_registry)

    print()
    print("✅ Migración completa!")
    print()
    print("📊 Estadísticas:")
    print(f"  Nodes: {len(schema.nodes)}")
    print(f"    - Events: {sum(1 for n in schema.nodes.values() if isinstance(n, EventNode))}")
    print(f"    - Entities: {sum(1 for n in schema.nodes.values() if isinstance(n, EntityNode))}")
    print(f"  AttributeFacts: {len(schema.attribute_facts)}")
    print(f"  RelationshipFacts: {len(schema.relationship_facts)}")
    print()

    # Export to JSON
    schema_dict = schema.to_dict()

    # Add metadata
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "source": "canonical_ledger_v6",
        "schema_version": "1.0",
        "description": "Full schema migration with EventNodes, AttributeFacts, and RelationshipFacts",
        "statistics": {
            "total_nodes": len(schema.nodes),
            "event_nodes": sum(1 for n in schema.nodes.values() if isinstance(n, EventNode)),
            "entity_nodes": sum(1 for n in schema.nodes.values() if isinstance(n, EntityNode)),
            "attribute_facts": len(schema.attribute_facts),
            "relationship_facts": len(schema.relationship_facts)
        },
        **schema_dict
    }

    # Save
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"💾 Guardado en: {output_path}")
    print(f"📦 Tamaño: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    print("🎉 ¡Migración completada con éxito!")


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "canonical" / "canonical_ledger_v6.json"
    output_path = base_dir / "data" / "canonical" / "canonical_ledger_schema_v1.json"

    # Run migration
    migrate_canonical_ledger(input_path, output_path)
