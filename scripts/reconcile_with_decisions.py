#!/usr/bin/env python3
"""
Field-Level Reconciliation with ReconciliationDecision Tracking

Extends reconcile_field_level.py to create ReconciliationDecision objects
for full auditability and compliance with Objective Layer framework.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from storage.schema import ReconciliationDecision, StorageSchema

# Import reconciliation engine
from reconcile_field_level import (
    reconcile_observations,
    FIELD_SCHEMA,
    SOURCE_PRIORITY
)

try:
    from reconciliation_strategies import create_default_registry
    PLUGGABLE_STRATEGIES_AVAILABLE = True
except ImportError:
    PLUGGABLE_STRATEGIES_AVAILABLE = False
    create_default_registry = None


def create_reconciliation_decision(
    observations: List[Dict],
    canonical: Dict,
    decision_counter: int
) -> ReconciliationDecision:
    """
    Create ReconciliationDecision object from reconciliation result

    Args:
        observations: Input observations that were reconciled
        canonical: Output canonical transaction
        decision_counter: Counter for unique decision IDs

    Returns:
        ReconciliationDecision object
    """
    # Extract observation IDs
    obs_ids = [obs.get('observation_id') or obs.get('id') for obs in observations]

    # Build cluster metadata from observations
    cluster_metadata = {
        'observation_count': len(observations),
        'data_sources': list(set(obs.get('data_source', obs.get('observer', 'unknown').split('_v')[0]) for obs in observations)),
        'reconciliation_timestamp': datetime.now().isoformat()
    }

    # Build field-level strategies from canonical transaction
    field_strategies = {}
    created_statement_ids = []

    for field_name in FIELD_SCHEMA.keys():
        if field_name in canonical:
            field_data = canonical[field_name]

            # Handle both dict and non-dict field values
            if isinstance(field_data, dict):
                strategy = field_data.get('reconciliation_method', 'unknown')
                chosen_obs = field_data.get('source_observation_id', 'unknown')
                confidence = field_data.get('confidence', 1.0)

                field_strategies[field_name] = {
                    'strategy': strategy,
                    'chosen_obs': chosen_obs,
                    'confidence': confidence,
                    'alternatives': field_data.get('alternatives', [])
                }

                # Generate statement ID for this field
                statement_id = f"attr_{canonical['id']}_{field_name}"
                created_statement_ids.append(statement_id)

    # Calculate overall confidence (average of field confidences)
    confidences = [fs['confidence'] for fs in field_strategies.values() if 'confidence' in fs]
    overall_confidence = sum(confidences) / len(confidences) if confidences else 1.0

    # Determine decision method
    if len(observations) == 1:
        decision_method = "single_source"
    else:
        decision_method = "automated"

    # Create ReconciliationDecision object
    decision = ReconciliationDecision(
        decision_id=f"recon_decision_{decision_counter:06d}",
        timestamp=datetime.now().isoformat(),
        observation_ids=obs_ids,
        cluster_metadata=cluster_metadata,
        field_strategies=field_strategies,
        created_statement_ids=created_statement_ids,
        confidence=overall_confidence,
        decision_method=decision_method
    )

    return decision


def main():
    """
    Process raw ledger with field-level reconciliation + ReconciliationDecision tracking
    """
    base_dir = Path(__file__).parent.parent

    # Load observations
    observations_file = base_dir / 'data' / 'observations' / 'raw_observations.json'

    if not observations_file.exists():
        print("⚠️  raw_observations.json not found, falling back to combined_raw_ledger.json")
        observations_file = base_dir / 'data' / 'raw-ledgers' / 'combined_raw_ledger.json'

    if not observations_file.exists():
        print(f"❌ No observation data found")
        return

    print(f"📂 Loading observations: {observations_file.name}")
    with open(observations_file) as f:
        obs_data = json.load(f)

    # Handle different formats
    if 'observations' in obs_data:
        observations = obs_data['observations']
        print(f"📊 Found {len(observations)} observations (immutable observation layer)\n")
    else:
        observations = obs_data.get('all_transactions') or obs_data.get('transactions', [])
        print(f"📊 Found {len(observations)} observations (legacy format)\n")

    transactions = observations

    # Load overlap groups
    overlap_file = base_dir / 'data' / 'canonical' / 'overlap_groups.json'

    if overlap_file.exists():
        print("📂 Loading overlap groups...")
        with open(overlap_file) as f:
            overlap_data = json.load(f)
        overlap_groups = overlap_data.get('overlap_groups', [])
        print(f"   Found {len(overlap_groups)} overlap groups\n")
    else:
        print("⚠️  No overlap groups found. Run detect_overlaps.py first.\n")
        overlap_groups = []

    # Initialize strategy registry
    strategy_registry = None
    if PLUGGABLE_STRATEGIES_AVAILABLE:
        try:
            strategy_registry = create_default_registry()
            print(f"✅ Using pluggable strategy system\n")
        except Exception as e:
            print(f"⚠️  Could not initialize strategy registry: {e}\n")

    # Create observation index
    obs_by_id = {}
    for obs in transactions:
        obs_id = obs.get('observation_id') or obs.get('id')
        if obs_id:
            obs_by_id[obs_id] = obs

    # Track processed observations
    processed_obs_ids = set()

    print("🔄 Reconciling observations with ReconciliationDecision tracking...\n")

    canonical_transactions = []
    reconciliation_decisions = []
    decision_counter = 0

    # Process overlap groups (multi-source reconciliation)
    for group in overlap_groups:
        group_obs_ids = group['observation_ids']

        # Get all observations in this group
        group_observations = []
        for obs_id in group_obs_ids:
            if obs_id in obs_by_id:
                group_observations.append(obs_by_id[obs_id])
                processed_obs_ids.add(obs_id)

        if group_observations:
            # Multi-source reconciliation
            canonical = reconcile_observations(group_observations, strategy_registry)

            # Create ReconciliationDecision
            decision = create_reconciliation_decision(
                group_observations,
                canonical,
                decision_counter
            )
            decision_counter += 1

            # Link decision to canonical transaction
            canonical['reconciliation_decision_id'] = decision.decision_id

            canonical_transactions.append(canonical)
            reconciliation_decisions.append(decision)

            # Show progress for first few
            if len(canonical_transactions) <= 3:
                print(f"✅ Multi-source reconciliation: {canonical['id']}")
                print(f"   Decision ID: {decision.decision_id}")
                print(f"   Sources: {canonical['reconciliation_metadata']['data_sources']}")
                print(f"   Field strategies: {len(decision.field_strategies)}")
                print()

    # Process single-source observations
    single_source_count = 0
    for obs in transactions:
        obs_id = obs.get('observation_id') or obs.get('id')
        if obs_id not in processed_obs_ids:
            canonical = reconcile_observations([obs], strategy_registry)

            # Create ReconciliationDecision (even for single-source)
            decision = create_reconciliation_decision(
                [obs],
                canonical,
                decision_counter
            )
            decision_counter += 1

            # Link decision to canonical transaction
            canonical['reconciliation_decision_id'] = decision.decision_id

            canonical_transactions.append(canonical)
            reconciliation_decisions.append(decision)
            single_source_count += 1

            if single_source_count <= 3:
                print(f"✅ Single-source: {canonical['id']}")
                print(f"   Decision ID: {decision.decision_id}")
                print()

    # Save outputs
    output_dir = base_dir / 'data' / 'canonical'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save canonical ledger
    canonical_file = output_dir / 'canonical_ledger_with_decisions.json'
    canonical_output = {
        'generated_at': datetime.now().isoformat(),
        'version': '6.0',
        'reconciliation_type': 'field_level_with_decisions',
        'schema_version': FIELD_SCHEMA,
        'transaction_count': len(canonical_transactions),
        'decision_count': len(reconciliation_decisions),
        'transactions': canonical_transactions
    }

    with open(canonical_file, 'w') as f:
        json.dump(canonical_output, f, indent=2)

    # Save reconciliation decisions
    decisions_file = output_dir / 'reconciliation_decisions.json'
    decisions_output = {
        'generated_at': datetime.now().isoformat(),
        'version': '1.0',
        'decision_count': len(reconciliation_decisions),
        'decisions': [d.to_dict() for d in reconciliation_decisions]
    }

    with open(decisions_file, 'w') as f:
        json.dump(decisions_output, f, indent=2)

    print(f"\n✅ Reconciliation with decisions complete!")
    print(f"\n📊 Output Files:")
    print(f"   Canonical ledger: {canonical_file}")
    print(f"   Reconciliation decisions: {decisions_file}")
    print(f"\n📈 Statistics:")
    print(f"   Total canonical transactions: {len(canonical_transactions)}")
    print(f"   ReconciliationDecisions created: {len(reconciliation_decisions)}")
    print(f"   Multi-source events: {len(overlap_groups)}")
    print(f"   Single-source events: {single_source_count}")
    print(f"\n🎯 Auditability:")
    print(f"   Every canonical transaction has a ReconciliationDecision")
    print(f"   Field-level strategies are tracked")
    print(f"   Full provenance chain is maintained")
    print(f"\n💡 Query examples:")
    print(f"   'Why did we choose this amount?' → Check reconciliation_decision_id")
    print(f"   'What alternatives were rejected?' → See field_strategies.alternatives")


if __name__ == '__main__':
    main()
