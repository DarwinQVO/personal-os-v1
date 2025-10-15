#!/usr/bin/env python3
"""
Storage Schema for Entity-Centric Architecture

Based on Eugenio's architecture:
- Entity Registry: persistent things (merchants, people, accounts)
- Event Store: occurrences (transactions, payments)
- AttributeFacts: scalar properties with provenance
- RelationshipFacts: connections between entities/events with provenance

All facts are immutable, bitemporal, and have full provenance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the registry"""
    ENTITY = "entity"
    EVENT = "event"
    SERIES = "series"


class EntityType(Enum):
    """Entity types"""
    MERCHANT = "Merchant"
    PERSON = "Person"
    ACCOUNT = "Account"
    LOCATION = "Location"
    ORGANIZATION = "Organization"
    OTHER = "Other"


class SeriesType(Enum):
    """Series types (recurring patterns)"""
    BNPL = "bnpl"  # Buy Now Pay Later (e.g., 8sleep)
    INSTALLMENT = "installment"  # Split payments (e.g., iPhone)
    PHONE_PLAN = "phone_plan"  # Phone contracts (e.g., ATT, Verizon)
    LEASE = "lease"  # Rent/leases (e.g., MiniBodega, DepaCuerna)
    CONTRACT = "contract"  # Service contracts (e.g., Darwin)
    SAAS_SUBSCRIPTION = "saas_subscription"  # Software subscriptions
    INSURANCE = "insurance"  # Insurance premiums
    TAX = "tax"  # Tax payments
    LOAN_PAYMENT = "loan_payment"  # Recurring loan payments
    UTILITY = "utility"  # Utilities (water, gas, electric)
    OTHER = "other"


class SeriesStatus(Enum):
    """Lifecycle status of a series"""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EventType(Enum):
    """Event types"""
    FINANCE_TRANSACTION = "finance_transaction"
    PAYMENT = "payment"
    TRANSFER = "transfer"


class NodeStatus(Enum):
    """Node status"""
    DRAFT = "draft"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


@dataclass
class Provenance:
    """Provenance tracking for facts"""
    observation_ids: List[str]
    source_method: str
    observer: str
    created_at: str
    confidence: float
    source_document: Optional[Dict[str, Any]] = None


@dataclass
class TemporalQualifiers:
    """Bitemporal tracking"""
    valid_from: str  # When this was true in reality
    valid_to: Optional[str] = None  # When this stopped being true
    observed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    superseded_at: Optional[str] = None  # When we learned this fact was wrong


@dataclass
class EntityNode:
    """
    Entity Registry Node

    Persistent things that exist over time.
    No embedded attributes - all properties stored in AttributeFacts.
    """
    entity_id: str
    type: EntityType
    status: NodeStatus = NodeStatus.VERIFIED
    aliases: List[str] = field(default_factory=list)
    external_ids: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_id': self.entity_id,
            'node_type': NodeType.ENTITY.value,
            'type': self.type.value,
            'status': self.status.value,
            'aliases': self.aliases,
            'external_ids': self.external_ids,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class EventNode:
    """
    Event Registry Node

    Occurrences that happen at specific times.
    Can have snapshot fields for performance (amount, happened_at),
    but these are materialized from AttributeFacts.
    """
    event_id: str
    event_type: EventType
    happened_at: str  # When the event occurred in reality
    status: NodeStatus = NodeStatus.VERIFIED

    # Snapshot fields (materialized from AttributeFacts for performance)
    snapshot: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'node_type': NodeType.EVENT.value,
            'event_type': self.event_type.value,
            'happened_at': self.happened_at,
            'status': self.status.value,
            'snapshot': self.snapshot,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class SeriesNode:
    """
    Series Registry Node

    Recurring patterns of events (subscriptions, installments, leases, etc.)
    Series are detected from EventNodes and track lifecycle.

    Example:
        Netflix subscription: monthly -$15.99 payments
        iPhone installment: 24 monthly payments of -$41.62
        Rent lease: monthly -$1,200 payments
    """
    series_id: str
    series_type: SeriesType
    status: SeriesStatus = SeriesStatus.ACTIVE

    # Pattern attributes
    frequency: str = "monthly"  # daily, weekly, monthly, quarterly, annual
    expected_amount: Optional[float] = None  # Expected amount (± tolerance)
    amount_tolerance: float = 0.10  # 10% tolerance by default

    # Temporal bounds
    start_date: Optional[str] = None  # First occurrence
    end_date: Optional[str] = None  # Last occurrence (or expected end)
    next_expected_date: Optional[str] = None  # When next payment is due

    # Relationships
    merchant_id: Optional[str] = None  # FK to EntityNode

    # Metadata
    events_count: int = 0  # Number of events in this series
    detection_confidence: float = 1.0  # Confidence in pattern detection

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'series_id': self.series_id,
            'node_type': NodeType.SERIES.value,
            'series_type': self.series_type.value,
            'status': self.status.value,
            'frequency': self.frequency,
            'expected_amount': self.expected_amount,
            'amount_tolerance': self.amount_tolerance,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'next_expected_date': self.next_expected_date,
            'merchant_id': self.merchant_id,
            'events_count': self.events_count,
            'detection_confidence': self.detection_confidence,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class AttributeFact:
    """
    Attribute Fact (subject-predicate-object triple)

    Stores scalar properties of entities/events/series.
    Each fact is immutable and has full provenance.

    Example:
        subject_id: "ent_merchant_safeway_123"
        predicate: "canonical_name"
        object: {"value": "Safeway", "type": "string"}
    """
    statement_id: str
    subject_id: str  # entity_id, event_id, or series_id
    predicate: str  # attribute name (e.g., "canonical_name", "amount")
    object: Dict[str, Any]  # {"value": ..., "type": "string|number|date|..."}

    # Qualifiers
    temporal: TemporalQualifiers
    provenance: Provenance

    # Reconciliation tracking
    reconciliation_decision_id: Optional[str] = None
    rejected_alternatives: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'statement_id': self.statement_id,
            'subject_id': self.subject_id,
            'predicate': self.predicate,
            'object': self.object,
            'temporal': {
                'valid_from': self.temporal.valid_from,
                'valid_to': self.temporal.valid_to,
                'observed_at': self.temporal.observed_at,
                'superseded_at': self.temporal.superseded_at
            },
            'provenance': {
                'observation_ids': self.provenance.observation_ids,
                'source_method': self.provenance.source_method,
                'observer': self.provenance.observer,
                'created_at': self.provenance.created_at,
                'confidence': self.provenance.confidence,
                'source_document': self.provenance.source_document
            },
            'reconciliation_decision_id': self.reconciliation_decision_id,
            'rejected_alternatives': self.rejected_alternatives
        }


@dataclass
class RelationshipFact:
    """
    Relationship Fact (subject-predicate-target triple)

    Stores connections between entities/events.
    Each relationship is first-class data with its own provenance.

    Example:
        subject_id: "evt_tx_991"
        predicate: "merchant"
        target_id: "ent_merchant_safeway_123"
    """
    statement_id: str
    subject_id: str  # source entity_id or event_id
    predicate: str  # relationship type (e.g., "merchant", "payer", "payee")
    target_id: str  # target entity_id or event_id

    # Qualifiers
    temporal: TemporalQualifiers
    provenance: Provenance

    # Reconciliation tracking
    reconciliation_decision_id: Optional[str] = None
    rejected_alternatives: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'statement_id': self.statement_id,
            'subject_id': self.subject_id,
            'predicate': self.predicate,
            'target_id': self.target_id,
            'temporal': {
                'valid_from': self.temporal.valid_from,
                'valid_to': self.temporal.valid_to,
                'observed_at': self.temporal.observed_at,
                'superseded_at': self.temporal.superseded_at
            },
            'provenance': {
                'observation_ids': self.provenance.observation_ids,
                'source_method': self.provenance.source_method,
                'observer': self.provenance.observer,
                'created_at': self.provenance.created_at,
                'confidence': self.provenance.confidence,
                'source_document': self.provenance.source_document
            },
            'reconciliation_decision_id': self.reconciliation_decision_id,
            'rejected_alternatives': self.rejected_alternatives
        }


@dataclass
class EntityLineage:
    """
    Entity Lineage - Tracks Entity ID Changes Over Time

    Never deletes entities, only marks as superseded.
    Tracks full history of entity merges and splits.

    Example:
        entity_uber_1, entity_uber_2, entity_uber_eats merged into entity_uber

        EntityLineage records:
        - old_entity_id: "entity_uber_1"
        - new_entity_id: "entity_uber"
        - operation: "merge"
        - timestamp: "2025-10-14T10:00:00Z"
        - reason: "Duplicate detection: similarity 0.92"
    """
    lineage_id: str
    timestamp: str

    # Entity change
    old_entity_id: str
    new_entity_id: str
    operation: str  # "merge" | "split" | "rename" | "deprecate"

    # Context
    reason: str
    confidence: float
    performed_by: str  # "automated_merge" | "manual_review" | "user_correction"

    # Metadata
    affected_statement_ids: List[str] = field(default_factory=list)  # Facts that were updated
    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'lineage_id': self.lineage_id,
            'timestamp': self.timestamp,
            'old_entity_id': self.old_entity_id,
            'new_entity_id': self.new_entity_id,
            'operation': self.operation,
            'reason': self.reason,
            'confidence': self.confidence,
            'performed_by': self.performed_by,
            'affected_statement_ids': self.affected_statement_ids,
            'metadata': self.metadata,
            'created_at': self.created_at
        }


@dataclass
class ReconciliationDecision:
    """
    Reconciliation Decision - First-Class Object

    Records how observations were consolidated into canonical facts.
    Makes reconciliation logic transparent and auditable.

    Example:
        Two observations of same transaction:
        - obs_bofa_001: amount=-100, description="Uber ride"
        - obs_wise_002: amount=-100, description="Uber Technologies"

        ReconciliationDecision records:
        - Which observations were consolidated
        - What strategy was used for each field
        - Why certain values were chosen over others
    """
    decision_id: str
    timestamp: str

    # Input observations
    observation_ids: List[str]
    cluster_metadata: Dict[str, Any]  # From overlap detection

    # Field-level decisions
    field_strategies: Dict[str, Dict[str, Any]]  # predicate -> strategy applied
    # Example: {
    #   "amount": {"strategy": "first_source", "chosen_obs": "obs_bofa_001"},
    #   "description": {"strategy": "most_complete", "chosen_obs": "obs_wise_002"}
    # }

    # Output facts created
    created_statement_ids: List[str]

    # Overall confidence
    confidence: float
    decision_method: str  # "automated" | "manual_review" | "human_override"

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp,
            'observation_ids': self.observation_ids,
            'cluster_metadata': self.cluster_metadata,
            'field_strategies': self.field_strategies,
            'created_statement_ids': self.created_statement_ids,
            'confidence': self.confidence,
            'decision_method': self.decision_method,
            'created_at': self.created_at
        }


@dataclass
class StorageSchema:
    """
    Complete storage schema

    Physical layout:
    ├── Node Registry (entities + events + series)
    ├── AttributeFacts (scalar properties)
    ├── RelationshipFacts (edges)
    ├── ReconciliationDecisions (audit trail)
    └── EntityLineage (entity ID change history)
    """
    nodes: Dict[str, EntityNode | EventNode | SeriesNode] = field(default_factory=dict)
    attribute_facts: List[AttributeFact] = field(default_factory=list)
    relationship_facts: List[RelationshipFact] = field(default_factory=list)
    reconciliation_decisions: List[ReconciliationDecision] = field(default_factory=list)
    entity_lineage: List[EntityLineage] = field(default_factory=list)

    def add_entity(self, entity: EntityNode) -> None:
        """Add entity to registry"""
        self.nodes[entity.entity_id] = entity

    def add_event(self, event: EventNode) -> None:
        """Add event to registry"""
        self.nodes[event.event_id] = event

    def add_series(self, series: SeriesNode) -> None:
        """Add series to registry"""
        self.nodes[series.series_id] = series

    def add_attribute_fact(self, fact: AttributeFact) -> None:
        """Add attribute fact"""
        self.attribute_facts.append(fact)

    def add_relationship_fact(self, fact: RelationshipFact) -> None:
        """Add relationship fact"""
        self.relationship_facts.append(fact)

    def add_reconciliation_decision(self, decision: ReconciliationDecision) -> None:
        """Add reconciliation decision"""
        self.reconciliation_decisions.append(decision)

    def add_entity_lineage(self, lineage: EntityLineage) -> None:
        """Add entity lineage record"""
        self.entity_lineage.append(lineage)

    def get_node(self, node_id: str) -> Optional[EntityNode | EventNode | SeriesNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    def get_entity_lineage(self, entity_id: str) -> List[EntityLineage]:
        """Get lineage history for an entity"""
        lineage = []
        for record in self.entity_lineage:
            if record.old_entity_id == entity_id or record.new_entity_id == entity_id:
                lineage.append(record)
        return lineage

    def resolve_current_entity_id(self, entity_id: str) -> str:
        """
        Resolve an entity ID to its current canonical ID

        Follows lineage chain: old_id -> new_id -> newer_id -> ...
        """
        current_id = entity_id
        visited = set()

        while current_id not in visited:
            visited.add(current_id)
            found_newer = False

            for record in self.entity_lineage:
                if record.old_entity_id == current_id:
                    current_id = record.new_entity_id
                    found_newer = True
                    break

            if not found_newer:
                break

        return current_id

    def get_attributes(self, subject_id: str, predicate: Optional[str] = None) -> List[AttributeFact]:
        """Get attribute facts for a subject"""
        facts = [f for f in self.attribute_facts if f.subject_id == subject_id]
        if predicate:
            facts = [f for f in facts if f.predicate == predicate]
        return facts

    def get_relationships(self, subject_id: str, predicate: Optional[str] = None) -> List[RelationshipFact]:
        """Get relationship facts for a subject"""
        facts = [f for f in self.relationship_facts if f.subject_id == subject_id]
        if predicate:
            facts = [f for f in facts if f.predicate == predicate]
        return facts

    def get_reconciliation_decision(self, decision_id: str) -> Optional[ReconciliationDecision]:
        """Get reconciliation decision by ID"""
        for decision in self.reconciliation_decisions:
            if decision.decision_id == decision_id:
                return decision
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            'nodes': {
                node_id: node.to_dict()
                for node_id, node in self.nodes.items()
            },
            'attribute_facts': [f.to_dict() for f in self.attribute_facts],
            'relationship_facts': [f.to_dict() for f in self.relationship_facts],
            'reconciliation_decisions': [d.to_dict() for d in self.reconciliation_decisions],
            'entity_lineage': [l.to_dict() for l in self.entity_lineage]
        }
