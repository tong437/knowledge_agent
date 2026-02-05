#!/usr/bin/env python3
"""
Quick integration test to verify the complete system works.
"""

import tempfile
import shutil
from pathlib import Path

from knowledge_agent.core import KnowledgeAgentCore
from knowledge_agent.models import DataSource, SourceType


def test_complete_integration():
    """Test the complete integrated system."""
    print("=" * 60)
    print("Testing Complete System Integration")
    print("=" * 60)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize the agent
        print("\n1. Initializing Knowledge Agent...")
        config = {
            "storage": {
                "type": "sqlite",
                "path": str(Path(temp_dir) / "test_knowledge.db")
            },
            "search": {
                "index_dir": str(Path(temp_dir) / "test_index")
            }
        }
        agent = KnowledgeAgentCore(config)
        print("   ✓ Agent initialized successfully")
        
        # Verify components
        print("\n2. Verifying Components...")
        assert agent._storage_manager is not None, "Storage manager not initialized"
        print("   ✓ Storage Manager")
        assert agent._knowledge_organizer is not None, "Knowledge organizer not initialized"
        print("   ✓ Knowledge Organizer")
        assert agent._search_engine is not None, "Search engine not initialized"
        print("   ✓ Search Engine")
        assert len(agent._data_processors) > 0, "No data processors initialized"
        print(f"   ✓ Data Processors ({len(agent._data_processors)} registered)")
        assert agent._data_import_export is not None, "Data import/export not initialized"
        print("   ✓ Data Import/Export")
        
        # Test knowledge collection
        print("\n3. Testing Knowledge Collection...")
        test_file = Path(temp_dir) / "test_document.txt"
        test_file.write_text("This is a test document about Python programming and machine learning.")
        
        source = DataSource(
            source_type=SourceType.DOCUMENT,
            path=str(test_file),
            metadata={"test": True}
        )
        
        item = agent.collect_knowledge(source)
        print(f"   ✓ Collected knowledge item: {item.id}")
        print(f"   ✓ Title: {item.title}")
        
        # Test knowledge organization
        print("\n4. Testing Knowledge Organization...")
        org_result = agent.organize_knowledge(item)
        print(f"   ✓ Categories: {len(org_result['categories'])}")
        print(f"   ✓ Tags: {len(org_result['tags'])}")
        print(f"   ✓ Relationships: {len(org_result['relationships'])}")
        
        # Test search
        print("\n5. Testing Search...")
        search_results = agent.search_knowledge("Python programming")
        print(f"   ✓ Found {search_results['total_results']} results")
        print(f"   ✓ Search time: {search_results['search_time_ms']:.2f}ms")
        
        # Test statistics
        print("\n6. Testing Statistics...")
        stats = agent.get_statistics()
        print(f"   ✓ Total items: {stats['total_items']}")
        print(f"   ✓ Total categories: {stats['total_categories']}")
        print(f"   ✓ Total tags: {stats['total_tags']}")
        
        # Test export
        print("\n7. Testing Data Export...")
        exported_data = agent.export_data(format="json")
        print(f"   ✓ Exported {len(exported_data['knowledge_items'])} items")
        
        # Test shutdown
        print("\n8. Testing Shutdown...")
        agent.shutdown()
        print("   ✓ Agent shut down successfully")
        
        print("\n" + "=" * 60)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass  # Ignore cleanup errors on Windows


if __name__ == "__main__":
    success = test_complete_integration()
    exit(0 if success else 1)
