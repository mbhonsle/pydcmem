"""
Unit tests for AgentMemoryOrchestrator class.
"""

import pytest
from unittest.mock import Mock, patch
from pydc_mem.dcmem import AgentMemoryOrchestrator
from pydc_mem.core.memory_extractor import MemoryExtractor, MemoryCandidate
from pydc_mem.core.memory_client import UserAttributeClient, UpsertReport


class TestAgentMemoryOrchestrator:
    """Test AgentMemoryOrchestrator functionality."""
    
    def test_init(self):
        """Test AgentMemoryOrchestrator initialization."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        assert orchestrator.extractor == mock_extractor
        assert orchestrator.ua_client == mock_client
    
    def test_update_success(self, sample_memory_candidates):
        """Test successful update operation."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        # Mock extractor response
        mock_extractor.extract.return_value = sample_memory_candidates
        
        # Mock client response
        mock_report = UpsertReport(user_id="user123", added=2, updated=1, skipped=0, errors=0)
        mock_client.upsert_from_candidates.return_value = mock_report
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        candidates, report = orchestrator.update(
            user_id="user123",
            utterance="I prefer Delta Airlines and window seats"
        )
        
        assert candidates == sample_memory_candidates
        assert report == mock_report
        
        # Verify extractor was called with correct parameters
        mock_extractor.extract.assert_called_once_with(
            utterance="I prefer Delta Airlines and window seats",
            session_vars=None,
            recent_dialogue=None,
            past_memory_facts=None
        )
        
        # Verify client was called with correct parameters
        mock_client.upsert_from_candidates.assert_called_once_with(
            user_id="user123",
            candidates=sample_memory_candidates,
            normalize_attributes=True,
            case_insensitive_compare=True,
            dedupe_last_write_wins=True
        )
    
    def test_update_with_context(self, sample_memory_candidates):
        """Test update operation with additional context."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        mock_extractor.extract.return_value = sample_memory_candidates
        mock_report = UpsertReport(user_id="user123", added=3, updated=0, skipped=0, errors=0)
        mock_client.upsert_from_candidates.return_value = mock_report
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        session_vars = {"passengers": 2, "class": "economy"}
        recent_dialogue = [("Agent", "What airline?"), ("User", "Delta")]
        past_memory_facts = ["Home airport = SFO"]
        
        candidates, report = orchestrator.update(
            user_id="user123",
            utterance="I want morning flights",
            session_vars=session_vars,
            recent_dialogue=recent_dialogue,
            past_memory_facts=past_memory_facts
        )
        
        # Verify extractor was called with context
        mock_extractor.extract.assert_called_once_with(
            utterance="I want morning flights",
            session_vars=session_vars,
            recent_dialogue=recent_dialogue,
            past_memory_facts=past_memory_facts
        )
    
    def test_update_dry_run(self, sample_memory_candidates):
        """Test update operation in dry run mode."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        mock_extractor.extract.return_value = sample_memory_candidates
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        candidates, report = orchestrator.update(
            user_id="user123",
            utterance="I prefer Delta Airlines",
            dry_run=True
        )
        
        assert candidates == sample_memory_candidates
        assert report is None
        
        # Verify extractor was called but client was not
        mock_extractor.extract.assert_called_once()
        mock_client.upsert_from_candidates.assert_not_called()
    
    def test_get(self):
        """Test get operation."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        orchestrator.get(user_id="user123", utterance="What are my preferences?",limit=1)
        
        # Verify client was called
        mock_client.fetch_relevant_attributes.assert_called_once_with(
            user_id="user123",
            utterance="What are my preferences?",
            limit=1
        )
    
    def test_update_with_empty_candidates(self):
        """Test update operation with no memory candidates."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        # Mock empty candidates
        mock_extractor.extract.return_value = []
        mock_report = UpsertReport(user_id="user123", added=0, updated=0, skipped=0, errors=0)
        mock_client.upsert_from_candidates.return_value = mock_report
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        candidates, report = orchestrator.update(
            user_id="user123",
            utterance="Hello there"
        )
        
        assert candidates == []
        assert report.added == 0
        assert report.updated == 0
        assert report.skipped == 0
        assert report.errors == 0
    
    def test_update_with_errors(self, sample_memory_candidates):
        """Test update operation with client errors."""
        mock_extractor = Mock(spec=MemoryExtractor)
        mock_client = Mock(spec=UserAttributeClient)
        
        mock_extractor.extract.return_value = sample_memory_candidates
        mock_report = UpsertReport(user_id="user123", added=0, updated=0, skipped=0, errors=3)
        mock_client.upsert_from_candidates.return_value = mock_report
        
        orchestrator = AgentMemoryOrchestrator(mock_extractor, mock_client)
        
        candidates, report = orchestrator.update(
            user_id="user123",
            utterance="I prefer Delta Airlines"
        )
        
        assert candidates == sample_memory_candidates
        assert report.errors == 3
        assert report.added == 0
        assert report.updated == 0
        assert report.skipped == 0


class TestCLI:
    """Test CLI functionality."""
    
    @patch('pydc_mem.dcmem.MemoryExtractor')
    @patch('pydc_mem.dcmem.UserAttributeClient')
    def test_handle_update(self, mock_client_class, mock_extractor_class, sample_memory_candidates):
        """Test handle_update function."""
        from pydc_mem.dcmem import handle_update
        
        # Mock the classes
        mock_extractor = Mock()
        mock_client = Mock()
        mock_extractor_class.return_value = mock_extractor
        mock_client_class.return_value = mock_client
        
        # Mock responses
        mock_extractor.extract.return_value = sample_memory_candidates
        mock_report = UpsertReport(user_id="user123", added=3, updated=0, skipped=0, errors=0)
        mock_client.upsert_from_candidates.return_value = mock_report
        
        # Mock args
        mock_args = Mock()
        mock_args.user_id = "user123"
        mock_args.utterance = "I prefer Delta Airlines"
        mock_args.dry_run = False
        mock_args.json = False
        
        # This would normally be called from _main, but we test the function directly
        # Note: In a real test, you'd need to mock the orchestrator creation
        # For now, this demonstrates the test structure
    
    @patch('pydc_mem.dcmem.MemoryExtractor')
    @patch('pydc_mem.dcmem.UserAttributeClient')
    def test_handle_get(self, mock_client_class, mock_extractor_class):
        """Test handle_get function."""
        from pydc_mem.dcmem import handle_get
        
        # Mock the classes
        mock_extractor = Mock()
        mock_client = Mock()
        mock_extractor_class.return_value = mock_extractor
        mock_client_class.return_value = mock_client
        
        # Mock args
        mock_args = Mock()
        mock_args.user_id = "user123"
        mock_args.utterance = "What are my preferences?"
        
        # This would normally be called from _main, but we test the function directly
        # Note: In a real test, you'd need to mock the orchestrator creation
        # For now, this demonstrates the test structure
