#!/usr/bin/env python3
"""
Hybrid Entity Resolution with EntityLineage Tracking

Extends hybrid_entity_resolution.py to create EntityLineage objects
for full auditability of entity ID changes.
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from storage.schema import EntityLineage, StorageSchema

# Import original hybrid resolver
from hybrid_entity_resolution import (
    BatchEntityClusterer,
    HybridEntityResolver,
    EntityMergeJob,
    MerchantNormalizer,
    SequenceMatcher
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class EntityMergeJobWithLineage(EntityMergeJob):
    """
    Extended EntityMergeJob that tracks lineage with EntityLineage objects
    """

    def __init__(self, entities_file: Path):
        super().__init__(entities_file)
        self.entity_lineages = []
        self.lineage_counter = 0

    def run_merge_with_lineage(self) -> Dict:
        """
        Detect and merge duplicate entities with lineage tracking

        Returns:
            Merge report with lineage records
        """
        logging.info("="*80)
        logging.info("PHASE 3: PERIODIC ENTITY MERGE (WITH LINEAGE)")
        logging.info("="*80)

        # Load entities
        logging.info(f"Loading entities from {self.entities_file}")
        with open(self.entities_file) as f:
            data = json.load(f)

        entities = data.get('entities', {})
        logging.info(f"Loaded {len(entities)} entities")

        # Find duplicate pairs
        duplicates = self._find_duplicates(entities)
        logging.info(f"Found {len(duplicates)} duplicate pairs")

        if not duplicates:
            logging.info("✅ No duplicates found - entities are clean")
            return {
                'duplicates_found': 0,
                'entities_merged': 0,
                'lineage_records': 0
            }

        # Merge duplicates WITH lineage tracking
        merged_entities, merge_log = self._merge_duplicates_with_lineage(entities, duplicates)

        # Save merged entities
        backup_file = self.entities_file.with_suffix('.json.backup')
        logging.info(f"Creating backup: {backup_file}")
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)

        data['entities'] = merged_entities
        data['last_merge'] = datetime.now().isoformat()

        with open(self.entities_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Save entity lineage
        lineage_file = self.entities_file.parent / 'entity_lineage.json'
        lineage_output = {
            'generated_at': datetime.now().isoformat(),
            'version': '1.0',
            'lineage_count': len(self.entity_lineages),
            'lineage': [l.to_dict() for l in self.entity_lineages]
        }

        with open(lineage_file, 'w') as f:
            json.dump(lineage_output, f, indent=2)

        # Save merge report
        report_file = self.entities_file.parent / 'entity_merge_report.json'
        report = {
            'timestamp': datetime.now().isoformat(),
            'duplicates_found': len(duplicates),
            'entities_before': len(entities),
            'entities_after': len(merged_entities),
            'entities_merged': len(entities) - len(merged_entities),
            'lineage_records_created': len(self.entity_lineages),
            'merge_log': merge_log
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logging.info(f"✅ Merge with lineage complete")
        logging.info(f"   Duplicates found: {len(duplicates)}")
        logging.info(f"   Entities before: {len(entities)}")
        logging.info(f"   Entities after: {len(merged_entities)}")
        logging.info(f"   Lineage records: {len(self.entity_lineages)}")
        logging.info(f"   Merge report: {report_file}")
        logging.info(f"   Lineage file: {lineage_file}")

        return report

    def _merge_duplicates_with_lineage(
        self,
        entities: Dict,
        duplicates: List[Tuple]
    ) -> Tuple[Dict, List]:
        """
        Merge duplicate entities WITH EntityLineage tracking

        Returns:
            (merged_entities, merge_log)
        """
        merged_entities = entities.copy()
        merge_log = []
        merged_ids = set()

        for id1, id2, similarity in duplicates:
            if id1 in merged_ids or id2 in merged_ids:
                continue

            # Determine primary entity (prefer one with more transactions)
            entity1 = merged_entities[id1]
            entity2 = merged_entities[id2]

            tx_count1 = entity1.get('transaction_count', 0)
            tx_count2 = entity2.get('transaction_count', 0)

            if tx_count1 >= tx_count2:
                primary_id = id1
                secondary_id = id2
                primary = entity1
                secondary = entity2
            else:
                primary_id = id2
                secondary_id = id1
                primary = entity2
                secondary = entity1

            # 🆕 CREATE ENTITY LINEAGE RECORD
            lineage = EntityLineage(
                lineage_id=f"lineage_{self.lineage_counter:06d}",
                timestamp=datetime.now().isoformat(),
                old_entity_id=secondary_id,
                new_entity_id=primary_id,
                operation="merge",
                reason=f"Duplicate detection: similarity {similarity:.2f}",
                confidence=similarity,
                performed_by="automated_merge",
                affected_statement_ids=[],  # Would track facts that were updated
                metadata={
                    'merged_canonical_name': secondary.get('canonical_name'),
                    'primary_canonical_name': primary.get('canonical_name'),
                    'transaction_count_transferred': tx_count2,
                    'amount_transferred': secondary.get('total_amount_usd', 0)
                }
            )

            self.entity_lineages.append(lineage)
            self.lineage_counter += 1

            # Merge data
            primary['aliases'] = list(set(
                primary.get('aliases', []) +
                secondary.get('aliases', []) +
                [secondary.get('canonical_name', '')]
            ))

            primary['transaction_count'] = (
                primary.get('transaction_count', 0) +
                secondary.get('transaction_count', 0)
            )

            primary['total_amount_usd'] = (
                primary.get('total_amount_usd', 0) +
                secondary.get('total_amount_usd', 0)
            )

            # Track lineage in entity
            primary['merged_from'] = primary.get('merged_from', []) + [secondary_id]
            primary['last_merged'] = datetime.now().isoformat()
            primary['lineage_id'] = lineage.lineage_id

            # Update merged entities
            merged_entities[primary_id] = primary

            # DON'T DELETE - mark as superseded (preserve history)
            secondary['status'] = 'superseded'
            secondary['superseded_by'] = primary_id
            secondary['superseded_at'] = datetime.now().isoformat()
            secondary['lineage_id'] = lineage.lineage_id
            merged_entities[secondary_id] = secondary  # Keep it!

            # Log merge
            merge_log.append({
                'primary': primary_id,
                'secondary': secondary_id,
                'similarity': similarity,
                'timestamp': datetime.now().isoformat(),
                'lineage_id': lineage.lineage_id
            })

        return merged_entities, merge_log


def main():
    """CLI for running hybrid entity resolution with lineage"""

    base_dir = Path(__file__).parent.parent

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python hybrid_entity_resolution_with_lineage.py batch   # Run batch pre-clustering")
        print("  python hybrid_entity_resolution_with_lineage.py merge   # Run periodic merge WITH lineage")
        print("  python hybrid_entity_resolution_with_lineage.py test    # Test resolution")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'batch':
        # Phase 1: Batch pre-clustering (same as original)
        raw_ledger = base_dir / 'data' / 'raw-ledgers' / 'combined_raw_ledger.json'
        output_dir = base_dir / 'data' / 'entity-storage'

        clusterer = BatchEntityClusterer(raw_ledger, output_dir)
        result = clusterer.run_batch_clustering()

        print("\n" + "="*80)
        print("📊 BATCH CLUSTERING COMPLETE")
        print("="*80)
        print(f"Entities: {result['entity_count']}")
        print(f"Transactions: {result['entity_stats']['total_transactions']}")

    elif command == 'merge':
        # Phase 3: Periodic merge WITH lineage tracking
        entities_file = base_dir / 'data' / 'entity-storage' / 'entities_batch_clustered.json'

        if not entities_file.exists():
            # Try regular entities.json
            entities_file = base_dir / 'data' / 'entity-storage' / 'nodes' / 'entities.json'

        if not entities_file.exists():
            print(f"❌ Entities file not found")
            print("Run 'batch' command first")
            sys.exit(1)

        merge_job = EntityMergeJobWithLineage(entities_file)
        report = merge_job.run_merge_with_lineage()

        print("\n" + "="*80)
        print("📊 MERGE JOB WITH LINEAGE COMPLETE")
        print("="*80)
        print(f"Duplicates found: {report['duplicates_found']}")
        print(f"Entities merged: {report.get('entities_merged', 0)}")
        print(f"Lineage records: {report.get('lineage_records_created', 0)}")
        print(f"Entities before: {report.get('entities_before', 0)}")
        print(f"Entities after: {report.get('entities_after', 0)}")
        print()
        print("🎯 Auditability:")
        print("   ✅ Entity lineage tracked")
        print("   ✅ Superseded entities preserved (not deleted)")
        print("   ✅ Full merge history available")

    elif command == 'test':
        # Test resolution (same as original)
        print("🧪 Testing Hybrid Entity Resolution\n")

        resolver = HybridEntityResolver()

        test_merchants = [
            "AMAZON.COM",
            "Amazon Mexico",
            "UBER *EATS",
            "Starbucks"
        ]

        for merchant in test_merchants:
            entity_id, method, confidence = resolver.resolve(merchant)
            print(f"{merchant:40s} → {entity_id:30s} ({confidence:.2f})")

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
